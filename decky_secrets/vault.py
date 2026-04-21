from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crypto import AuthTagError, encrypt_aes_gcm, decrypt_aes_gcm

VAULT_DIR_NAME = ".decky-secrets"
VAULT_FILE_NAME = "vault"
VAULT_MAGIC = "DSV1"
CURRENT_BLOB_VERSION = 1
CURRENT_KDF_ALGORITHM = "pbkdf2-sha256"
CURRENT_KDF_ITERATIONS = 600_000
CURRENT_PIN_KDF_ITERATIONS = 200_000
AES_GCM_ALGORITHM = "aes-256-gcm"
SALT_SIZE = 16
NONCE_SIZE = 12
DEFAULT_RECORDS: list[dict[str, Any]] = []


class VaultBlobError(Exception):
    pass


@dataclass(frozen=True)
class VaultPayloadVault:
    created_at: str
    updated_at: str
    version: int = CURRENT_BLOB_VERSION


@dataclass(frozen=True)
class VaultPayloadPin:
    value: str
    kdf: dict[str, Any]


@dataclass(frozen=True)
class VaultRecord:
    key: str
    name: str
    username: str | None
    secret: str
    notes: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class VaultPayload:
    vault: VaultPayloadVault
    pin: VaultPayloadPin
    records: list[dict[str, Any]]
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VaultPayload":
        try:
            vault = payload["vault"]
            pin = payload["pin"]
            records = payload["records"]
        except KeyError as exc:
            raise VaultBlobError(f"vault payload missing field: {exc.args[0]}") from exc

        if not isinstance(records, list):
            raise VaultBlobError("vault payload records must be a list")

        return cls(
            vault=VaultPayloadVault(**vault),
            pin=VaultPayloadPin(**pin),
            records=[_normalize_record(record) for record in records],
            settings=payload.get("settings", {}),
        )


class VaultFileStore:
    def __init__(self, home_dir: Path | None = None) -> None:
        self.home_dir = home_dir or Path.home()
        self.vault_dir = self.home_dir / VAULT_DIR_NAME
        self.vault_path = self.vault_dir / VAULT_FILE_NAME

    def create_vault(
        self,
        *,
        master_password: str,
        pin: str,
        records: list[dict[str, Any]] | None = None,
        now: str | None = None,
    ) -> VaultPayload:
        _validate_master_password(master_password)
        pin_kdf = _create_pin_kdf(pin)
        timestamp = now or _utc_now()
        payload = VaultPayload(
            vault=VaultPayloadVault(created_at=timestamp, updated_at=timestamp),
            pin=VaultPayloadPin(value=pin, kdf=pin_kdf),
            records=[_normalize_record(record, default_timestamp=timestamp) for record in (records or DEFAULT_RECORDS)],
            settings={},
        )
        self.save_vault(payload, master_password=master_password)
        return payload

    def load_vault(self, *, master_password: str) -> VaultPayload:
        blob = self._read_blob()
        plaintext_buffer = bytearray(self._decrypt_blob(blob=blob, master_password=master_password))
        try:
            payload_dict = json.loads(plaintext_buffer.decode("utf-8"))
            return VaultPayload.from_dict(payload_dict)
        except json.JSONDecodeError as exc:
            raise VaultBlobError("vault payload is not valid JSON") from exc
        finally:
            _wipe_bytes(plaintext_buffer)

    def save_vault(self, payload: VaultPayload, *, master_password: str) -> None:
        _validate_master_password(master_password)
        _validate_payload(payload)
        self._ensure_storage_permissions()

        salt = secrets.token_bytes(SALT_SIZE)
        nonce = secrets.token_bytes(NONCE_SIZE)
        key = _derive_key(master_password=master_password, salt=salt, iterations=CURRENT_KDF_ITERATIONS)
        plaintext_buffer = bytearray(json.dumps(payload.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        try:
            ciphertext = encrypt_aes_gcm(key=key, nonce=nonce, plaintext=bytes(plaintext_buffer))
        finally:
            _wipe_bytes(plaintext_buffer)
            _wipe_bytes(key)

        blob = {
            "magic": VAULT_MAGIC,
            "version": CURRENT_BLOB_VERSION,
            "kdf": {
                "algorithm": CURRENT_KDF_ALGORITHM,
                "iterations": CURRENT_KDF_ITERATIONS,
                "salt_b64": _b64encode(salt),
            },
            "cipher": {
                "algorithm": AES_GCM_ALGORITHM,
                "nonce_b64": _b64encode(nonce),
            },
            "ciphertext_b64": _b64encode(ciphertext),
        }
        self._write_blob(blob)

    def _ensure_storage_permissions(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.vault_dir, 0o700)

    def _read_blob(self) -> dict[str, Any]:
        if not self.vault_path.exists():
            raise VaultBlobError(f"vault file does not exist at {self.vault_path}")

        try:
            raw = self.vault_path.read_text(encoding="utf-8")
            blob = json.loads(raw)
        except OSError as exc:
            raise VaultBlobError("failed to read vault file") from exc
        except json.JSONDecodeError as exc:
            raise VaultBlobError("vault blob is not valid JSON") from exc

        if blob.get("magic") != VAULT_MAGIC:
            raise VaultBlobError("vault blob has invalid magic")
        if blob.get("version") != CURRENT_BLOB_VERSION:
            raise VaultBlobError("vault blob version is unsupported")
        return blob

    def _decrypt_blob(self, *, blob: dict[str, Any], master_password: str) -> bytes:
        _validate_master_password(master_password)
        try:
            kdf = blob["kdf"]
            cipher = blob["cipher"]
            salt = _b64decode(kdf["salt_b64"])
            nonce = _b64decode(cipher["nonce_b64"])
            ciphertext = _b64decode(blob["ciphertext_b64"])
            iterations = int(kdf["iterations"])
        except (KeyError, ValueError, TypeError) as exc:
            raise VaultBlobError("vault blob header is invalid") from exc

        if kdf.get("algorithm") != CURRENT_KDF_ALGORITHM:
            raise VaultBlobError("vault blob uses unsupported KDF algorithm")
        if cipher.get("algorithm") != AES_GCM_ALGORITHM:
            raise VaultBlobError("vault blob uses unsupported cipher algorithm")

        key = _derive_key(master_password=master_password, salt=salt, iterations=iterations)
        try:
            return decrypt_aes_gcm(key=key, nonce=nonce, ciphertext_and_tag=ciphertext)
        except AuthTagError as exc:
            raise VaultBlobError("vault decryption failed") from exc
        finally:
            _wipe_bytes(key)

    def _write_blob(self, blob: dict[str, Any]) -> None:
        self._ensure_storage_permissions()
        encoded = json.dumps(blob, sort_keys=True, separators=(",", ":")).encode("utf-8")
        temp_fd, temp_path = tempfile.mkstemp(prefix="vault-", dir=self.vault_dir)
        try:
            os.fchmod(temp_fd, 0o600)
            with os.fdopen(temp_fd, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.vault_path)
            os.chmod(self.vault_path, 0o600)
        except Exception:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            raise


def create_recovery_key() -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    raw = "".join(secrets.choice(alphabet) for _ in range(32))
    return "-".join(raw[index : index + 4] for index in range(0, len(raw), 4))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _derive_key(*, master_password: str, salt: bytes, iterations: int) -> bytearray:
    if iterations <= 0:
        raise VaultBlobError("PBKDF2 iterations must be positive")
    return bytearray(
        hashlib.pbkdf2_hmac(
            "sha256",
            master_password.encode("utf-8"),
            salt,
            iterations,
            dklen=32,
        )
    )


def _create_pin_kdf(pin: str) -> dict[str, Any]:
    _validate_pin(pin)
    return {
        "algorithm": CURRENT_KDF_ALGORITHM,
        "iterations": CURRENT_PIN_KDF_ITERATIONS,
        "salt_b64": _b64encode(secrets.token_bytes(SALT_SIZE)),
    }


def _validate_master_password(master_password: str) -> None:
    if not isinstance(master_password, str) or not master_password:
        raise VaultBlobError("master password must be a non-empty string")


def _validate_pin(pin: str) -> None:
    if not isinstance(pin, str) or not pin.isdigit() or not 4 <= len(pin) <= 6:
        raise VaultBlobError("PIN must be numeric and 4 to 6 digits long")


def _validate_payload(payload: VaultPayload) -> None:
    _validate_pin(payload.pin.value)
    if payload.pin.kdf.get("algorithm") != CURRENT_KDF_ALGORITHM:
        raise VaultBlobError("PIN KDF algorithm is invalid")
    if int(payload.pin.kdf.get("iterations", 0)) != CURRENT_PIN_KDF_ITERATIONS:
        raise VaultBlobError("PIN KDF iterations are invalid")
    _b64decode(str(payload.pin.kdf.get("salt_b64", "")))
    if not payload.vault.created_at or not payload.vault.updated_at:
        raise VaultBlobError("vault timestamps are required")

    seen_keys: set[str] = set()
    for record in payload.records:
        normalized = _normalize_record(record)
        if normalized["key"] in seen_keys:
            raise VaultBlobError("record keys must be unique")
        seen_keys.add(normalized["key"])


def _normalize_record(record: dict[str, Any], default_timestamp: str | None = None) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise VaultBlobError("record must be an object")

    timestamp = default_timestamp or _utc_now()
    key = record.get("key")
    name = record.get("name")
    secret = record.get("secret")
    username = record.get("username")
    notes = record.get("notes", [])

    if not isinstance(key, str) or not key:
        raise VaultBlobError("record key must be a non-empty string")
    if not isinstance(name, str) or not name:
        raise VaultBlobError("record name must be a non-empty string")
    if username is not None and not isinstance(username, str):
        raise VaultBlobError("record username must be a string or null")
    if not isinstance(secret, str) or not secret:
        raise VaultBlobError("record secret must be a non-empty string")
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        raise VaultBlobError("record notes must be a string list")

    return {
        "key": key,
        "name": name,
        "username": username,
        "secret": secret,
        "notes": notes,
        "created_at": record.get("created_at") or timestamp,
        "updated_at": record.get("updated_at") or timestamp,
    }


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        raise VaultBlobError("vault blob base64 field is invalid") from exc


def _wipe_bytes(buffer: bytearray) -> None:
    for index in range(len(buffer)):
        buffer[index] = 0
