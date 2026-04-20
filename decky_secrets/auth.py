from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Literal

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .vault import CURRENT_KDF_ALGORITHM, CURRENT_PIN_KDF_ITERATIONS, NONCE_SIZE, VaultBlobError, VaultFileStore, VaultPayload

VaultState = Literal[
    "uninitialized_vault",
    "decrypt_required",
    "session_locked",
    "accessible",
    "relocking",
]
AuthFactor = Literal["master_password", "pin", "recovery_key"]
CallerType = Literal["ui", "cli", "internal"]

DEFAULT_SESSION_ACCESS_WINDOW_SECONDS = 60
DEFAULT_FULL_RELOCK_TIMEOUT_SECONDS = 6 * 60 * 60
DEFAULT_SHORT_WINDOW_ATTEMPTS = 5
DEFAULT_SHORT_WINDOW_SECONDS = 60
DEFAULT_LONG_WINDOW_ATTEMPTS = 20
DEFAULT_LONG_WINDOW_SECONDS = 10 * 60
DEFAULT_DELETE_ON_FAILURE_THRESHOLD = 40


class AuthenticationError(Exception):
    pass


class AuthenticationLockedError(AuthenticationError):
    def __init__(self, retry_at: datetime) -> None:
        super().__init__("authentication temporarily blocked")
        self.retry_at = retry_at


class AccessStateError(AuthenticationError):
    pass


@dataclass(frozen=True)
class AuthConfig:
    session_access_window_seconds: int = DEFAULT_SESSION_ACCESS_WINDOW_SECONDS
    full_relock_timeout_seconds: int = DEFAULT_FULL_RELOCK_TIMEOUT_SECONDS
    short_window_attempt_limit: int = DEFAULT_SHORT_WINDOW_ATTEMPTS
    short_window_seconds: int = DEFAULT_SHORT_WINDOW_SECONDS
    long_window_attempt_limit: int = DEFAULT_LONG_WINDOW_ATTEMPTS
    long_window_seconds: int = DEFAULT_LONG_WINDOW_SECONDS
    delete_on_failure: bool = False
    delete_on_failure_threshold: int = DEFAULT_DELETE_ON_FAILURE_THRESHOLD


@dataclass(frozen=True)
class FailureEvent:
    at: datetime
    factor: AuthFactor
    caller: CallerType


@dataclass(frozen=True)
class AuthStatus:
    state: VaultState
    vault_exists: bool
    session_access_expires_at: str | None
    full_relock_at: str | None
    auth_locked_until: str | None
    delete_on_failure_enabled: bool
    failure_count: int


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


@dataclass
class SessionEnvelope:
    nonce_b64: str
    ciphertext_b64: str
    pin_kdf: dict[str, Any]


class VaultAuthManager:
    def __init__(
        self,
        *,
        store: VaultFileStore | None = None,
        config: AuthConfig | None = None,
        clock: SystemClock | None = None,
    ) -> None:
        self.store = store or VaultFileStore()
        self.config = config or AuthConfig()
        self.clock = clock or SystemClock()
        self._session_envelope: SessionEnvelope | None = None
        self._accessible_since: datetime | None = None
        self._last_activity_at: datetime | None = None
        self._failures: list[FailureEvent] = []
        self._delete_failure_count = 0
        self._session_key: bytearray | None = None

    def get_status(self) -> AuthStatus:
        self._apply_timeouts()
        locked_until = self._current_lockout_until(self.clock.now())
        return AuthStatus(
            state=self._current_state(),
            vault_exists=self.store.vault_path.exists(),
            session_access_expires_at=_isoformat(self._session_access_deadline()),
            full_relock_at=_isoformat(self._full_relock_deadline()),
            auth_locked_until=_isoformat(locked_until),
            delete_on_failure_enabled=self.config.delete_on_failure,
            failure_count=self._delete_failure_count,
        )

    def unlock_with_password(self, *, master_password: str, caller: CallerType = "internal") -> AuthStatus:
        self._apply_timeouts()
        self._assert_not_locked_out()
        self._require_existing_vault()

        try:
            payload = self.store.load_vault(master_password=master_password)
        except VaultBlobError as exc:
            self._record_failure(factor="master_password", caller=caller)
            raise AuthenticationError("master password unlock failed") from exc

        self._session_envelope = self._create_session_envelope(payload=payload, pin=payload.pin.value)
        self._wipe_session_key()
        self._accessible_since = None
        self._last_activity_at = self.clock.now()
        self._clear_failures(reset_delete_counter=False)
        return self.get_status()

    def unlock_with_pin(self, *, pin: str, caller: CallerType = "internal") -> AuthStatus:
        self._apply_timeouts()
        self._assert_not_locked_out()
        if self._session_envelope is None:
            if self.store.vault_path.exists():
                raise AccessStateError("master password unlock required")
            raise AccessStateError("vault has not been initialized")

        session_key = _derive_pin_key(pin=pin, pin_kdf=self._session_envelope.pin_kdf)
        try:
            self._decrypt_session_payload(session_key=session_key)
        except (VaultBlobError, InvalidTag) as exc:
            _wipe_bytes(session_key)
            self._record_failure(factor="pin", caller=caller)
            raise AuthenticationError("PIN unlock failed") from exc

        self._wipe_session_key()
        self._session_key = session_key
        now = self.clock.now()
        self._accessible_since = now
        self._last_activity_at = now
        self._clear_failures(reset_delete_counter=False)
        return self.get_status()

    def authenticate_recovery_key(
        self,
        *,
        provided_recovery_key: str,
        expected_recovery_key: str,
        caller: CallerType = "internal",
    ) -> bool:
        self._apply_timeouts()
        self._assert_not_locked_out()
        if not secrets.compare_digest(provided_recovery_key, expected_recovery_key):
            self._record_failure(factor="recovery_key", caller=caller)
            raise AuthenticationError("recovery key authentication failed")

        self._clear_failures(reset_delete_counter=False)
        return True

    def access_vault(
        self,
        *,
        pin: str | None,
        caller: CallerType = "internal",
        operation: Callable[[VaultPayload], Any],
    ) -> Any:
        del pin, caller
        self._apply_timeouts()
        if self._current_state() != "accessible":
            raise AccessStateError("vault access requires an active unlocked session")
        if self._session_key is None:
            raise AccessStateError("active session key is unavailable")

        payload = self._decrypt_session_payload(session_key=self._session_key)
        try:
            result = operation(payload)
            refreshed_payload = VaultPayload.from_dict(payload.to_dict())
            self._session_envelope = self._create_session_envelope(payload=refreshed_payload, pin=refreshed_payload.pin.value)
            now = self.clock.now()
            self._last_activity_at = now
            self._accessible_since = now
            return result
        finally:
            _wipe_mapping(payload.to_dict())

    def lock_to_session(self) -> AuthStatus:
        self._apply_timeouts()
        if self._session_envelope is None:
            return self.get_status()
        self._wipe_session_key()
        self._accessible_since = None
        return self.get_status()

    def full_lock(self) -> AuthStatus:
        self._discard_session_material()
        return self.get_status()

    def record_restart(self) -> AuthStatus:
        self._discard_session_material()
        self._clear_failures(reset_delete_counter=False)
        return self.get_status()

    def _apply_timeouts(self) -> None:
        if self._session_envelope is None or self._last_activity_at is None:
            return

        now = self.clock.now()
        full_relock_deadline = self._full_relock_deadline()
        if full_relock_deadline is not None and now >= full_relock_deadline:
            self._discard_session_material()
            return

        session_deadline = self._session_access_deadline()
        if self._accessible_since is not None and session_deadline is not None and now >= session_deadline:
            self._wipe_session_key()
            self._accessible_since = None

    def _current_state(self) -> VaultState:
        if not self.store.vault_path.exists():
            return "uninitialized_vault"
        if self._session_envelope is None:
            return "decrypt_required"
        if self._accessible_since is None:
            return "session_locked"
        return "accessible"

    def _create_session_envelope(self, *, payload: VaultPayload, pin: str) -> SessionEnvelope:
        key = _derive_pin_key(pin=pin, pin_kdf=payload.pin.kdf)
        nonce = secrets.token_bytes(NONCE_SIZE)
        plaintext = bytearray(json.dumps(payload.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        try:
            ciphertext = AESGCM(bytes(key)).encrypt(nonce, bytes(plaintext), None)
        finally:
            _wipe_bytes(key)
            _wipe_bytes(plaintext)

        return SessionEnvelope(
            nonce_b64=base64.b64encode(nonce).decode("ascii"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
            pin_kdf=dict(payload.pin.kdf),
        )

    def _decrypt_session_payload(self, *, session_key: bytearray) -> VaultPayload:
        if self._session_envelope is None:
            raise AccessStateError("no active session envelope is available")

        plaintext = bytearray()
        try:
            plaintext_bytes = AESGCM(bytes(session_key)).decrypt(
                base64.b64decode(self._session_envelope.nonce_b64.encode("ascii")),
                base64.b64decode(self._session_envelope.ciphertext_b64.encode("ascii")),
                None,
            )
            plaintext.extend(plaintext_bytes)
            return VaultPayload.from_dict(json.loads(plaintext.decode("utf-8")))
        except InvalidTag as exc:
            raise VaultBlobError("session unlock failed") from exc
        finally:
            _wipe_bytes(plaintext)

    def _record_failure(self, *, factor: AuthFactor, caller: CallerType) -> None:
        now = self.clock.now()
        self._failures.append(FailureEvent(at=now, factor=factor, caller=caller))
        self._delete_failure_count += 1
        self._trim_failures(now)
        if self.config.delete_on_failure and self._delete_failure_count >= self.config.delete_on_failure_threshold:
            self._destroy_vault_file()
            self._discard_session_material()
            self._clear_failures(reset_delete_counter=True)
            raise AuthenticationError("vault destroyed after repeated authentication failures")

    def _trim_failures(self, now: datetime) -> None:
        oldest_allowed = now - timedelta(seconds=max(self.config.short_window_seconds, self.config.long_window_seconds))
        self._failures = [failure for failure in self._failures if failure.at >= oldest_allowed]

    def _current_lockout_until(self, now: datetime) -> datetime | None:
        self._trim_failures(now)
        lockouts: list[datetime] = []
        short_failures = [failure for failure in self._failures if failure.at >= now - timedelta(seconds=self.config.short_window_seconds)]
        if len(short_failures) >= self.config.short_window_attempt_limit:
            earliest = min(failure.at for failure in short_failures)
            lockouts.append(earliest + timedelta(seconds=self.config.short_window_seconds))

        long_failures = [failure for failure in self._failures if failure.at >= now - timedelta(seconds=self.config.long_window_seconds)]
        if len(long_failures) >= self.config.long_window_attempt_limit:
            earliest = min(failure.at for failure in long_failures)
            lockouts.append(earliest + timedelta(seconds=self.config.long_window_seconds))

        return max(lockouts) if lockouts else None

    def _assert_not_locked_out(self) -> None:
        retry_at = self._current_lockout_until(self.clock.now())
        if retry_at is not None:
            raise AuthenticationLockedError(retry_at=retry_at)

    def _clear_failures(self, *, reset_delete_counter: bool) -> None:
        self._failures.clear()
        if reset_delete_counter:
            self._delete_failure_count = 0

    def _require_existing_vault(self) -> None:
        if not self.store.vault_path.exists():
            raise AccessStateError("vault has not been initialized")

    def _session_access_deadline(self) -> datetime | None:
        if self._accessible_since is None:
            return None
        return self._last_activity_at + timedelta(seconds=self.config.session_access_window_seconds) if self._last_activity_at else None

    def _full_relock_deadline(self) -> datetime | None:
        if self._session_envelope is None or self._last_activity_at is None:
            return None
        return self._last_activity_at + timedelta(seconds=self.config.full_relock_timeout_seconds)

    def _discard_session_material(self) -> None:
        self._session_envelope = None
        self._wipe_session_key()
        self._accessible_since = None
        self._last_activity_at = None

    def _wipe_session_key(self) -> None:
        if self._session_key is not None:
            _wipe_bytes(self._session_key)
            self._session_key = None

    def _destroy_vault_file(self) -> None:
        try:
            if self.store.vault_path.exists():
                os.remove(self.store.vault_path)
        except FileNotFoundError:
            pass


def _derive_pin_key(*, pin: str, pin_kdf: dict[str, Any]) -> bytearray:
    if pin_kdf.get("algorithm") != CURRENT_KDF_ALGORITHM:
        raise VaultBlobError("unsupported PIN KDF algorithm")
    iterations = int(pin_kdf.get("iterations", 0))
    if iterations != CURRENT_PIN_KDF_ITERATIONS:
        raise VaultBlobError("unsupported PIN KDF iterations")
    salt_b64 = pin_kdf.get("salt_b64")
    if not isinstance(salt_b64, str):
        raise VaultBlobError("PIN KDF salt is invalid")
    salt = base64.b64decode(salt_b64.encode("ascii"), validate=True)
    return bytearray(hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, iterations, dklen=32))


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _wipe_bytes(buffer: bytearray) -> None:
    for index in range(len(buffer)):
        buffer[index] = 0


def _wipe_mapping(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            _wipe_mapping(nested)
    elif isinstance(value, list):
        for nested in value:
            _wipe_mapping(nested)
