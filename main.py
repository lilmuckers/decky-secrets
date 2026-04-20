from __future__ import annotations

import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import decky


def _ensure_plugin_root_on_sys_path() -> None:
    plugin_root = Path(__file__).resolve().parent
    plugin_root_str = str(plugin_root)
    if plugin_root_str not in sys.path:
        sys.path.insert(0, plugin_root_str)


_ensure_plugin_root_on_sys_path()

from decky_secrets import (
    BEST_EFFORT_CLEAR_DISCLAIMER,
    ClipboardCopyService,
    VaultAuthManager,
    VaultBlobError,
    VaultPayload,
    VaultState,
)
from decky_secrets.auth import AccessStateError, AuthenticationError, AuthenticationLockedError
from decky_secrets.vault import VAULT_FILE_NAME, _utc_now


@dataclass(frozen=True)
class RuntimeStatus:
    plugin: str
    version: str
    vault_state: VaultState
    backend_model: str
    notes: list[str]
    vault_path: str
    vault_exists: bool
    auth_locked_until: str | None
    session_access_expires_at: str | None
    full_relock_at: str | None
    session_pin_length: int | None
    clipboard_clear_seconds: int
    clipboard_clear_best_effort: bool
    clipboard_clear_disclaimer: str


class Plugin:
    def __init__(self, *, auth: VaultAuthManager | None = None, clipboard: ClipboardCopyService | None = None) -> None:
        self._auth = auth or VaultAuthManager()
        self._clipboard = clipboard or ClipboardCopyService(auth=self._auth)
        self._ui_master_password: bytearray | None = None

    async def get_status(self) -> dict:
        auth_status = self._auth.get_status()
        status = RuntimeStatus(
            plugin="decky-secrets",
            version="0.0.5",
            vault_state=auth_status.state,
            backend_model="python-auth-backend",
            notes=[
                "Routine list browsing stays non-secret until you explicitly reveal or copy a value.",
                "Password copy is an explicit UI action and clipboard clearing is best effort only.",
                "Manual lock returns to the session PIN flow while restart or full relock requires the master password again.",
                f"Vault file name is reserved as {VAULT_FILE_NAME} under ~/.decky-secrets/.",
            ],
            vault_path=str(self._auth.store.vault_path),
            vault_exists=auth_status.vault_exists,
            auth_locked_until=auth_status.auth_locked_until,
            session_access_expires_at=auth_status.session_access_expires_at,
            full_relock_at=auth_status.full_relock_at,
            session_pin_length=auth_status.session_pin_length,
            clipboard_clear_seconds=self._clipboard.clipboard_clear_seconds,
            clipboard_clear_best_effort=True,
            clipboard_clear_disclaimer=BEST_EFFORT_CLEAR_DISCLAIMER,
        )
        return asdict(status)

    async def create_vault(self, master_password: str, pin: str) -> dict:
        try:
            if self._auth.get_status().vault_exists:
                raise RuntimeError("vault already exists")
            self._auth.store.create_vault(master_password=master_password, pin=pin)
            self._cache_ui_master_password(master_password)
            self._auth.unlock_with_password(master_password=master_password, caller="ui")
            return asdict(self._auth.unlock_with_pin(pin=pin, caller="ui"))
        except (VaultBlobError, AuthenticationError, AccessStateError) as exc:
            raise RuntimeError(str(exc)) from exc

    async def unlock_with_master_password(self, master_password: str) -> dict:
        try:
            status = self._auth.unlock_with_password(master_password=master_password, caller="ui")
            self._cache_ui_master_password(master_password)
            return asdict(status)
        except (AuthenticationLockedError, AuthenticationError, AccessStateError) as exc:
            raise RuntimeError(str(exc)) from exc

    async def unlock_with_pin(self, pin: str) -> dict:
        try:
            return asdict(self._auth.unlock_with_pin(pin=pin, caller="ui"))
        except (AuthenticationLockedError, AuthenticationError, AccessStateError) as exc:
            raise RuntimeError(str(exc)) from exc

    async def lock_to_pin(self) -> dict:
        return asdict(self._auth.lock_to_session())

    async def full_lock(self) -> dict:
        self._wipe_ui_master_password()
        return asdict(self._auth.full_lock())

    async def list_records(self) -> list[dict]:
        try:
            return self._clipboard.list_records(caller="ui")
        except AccessStateError as exc:
            raise RuntimeError("vault access requires an active unlocked session") from exc

    async def get_record_detail(self, record_key: str) -> dict:
        def operation(payload: VaultPayload) -> dict[str, Any]:
            for record in payload.records:
                if record.get("key") == record_key:
                    return {
                        "key": str(record["key"]),
                        "name": str(record["name"]),
                        "username": record.get("username") if isinstance(record.get("username"), str) else None,
                        "notes": "\n".join(record.get("notes", [])),
                    }
            raise ValueError("record not found")

        try:
            return self._auth.access_vault(pin=None, caller="ui", operation=operation)
        except (AccessStateError, ValueError) as exc:
            raise RuntimeError("record detail unavailable") from exc

    async def reveal_record_secret(self, record_key: str) -> dict:
        def operation(payload: VaultPayload) -> dict[str, str]:
            for record in payload.records:
                if record.get("key") == record_key:
                    return {
                        "record_key": str(record["key"]),
                        "record_name": str(record["name"]),
                        "secret": str(record["secret"]),
                    }
            raise ValueError("record not found")

        try:
            return self._auth.access_vault(pin=None, caller="ui", operation=operation)
        except (AccessStateError, ValueError) as exc:
            raise RuntimeError("secret reveal failed") from exc

    async def save_record(
        self,
        record_key: str,
        name: str,
        username: str | None,
        secret: str,
        notes: str | None = None,
        existing_key: str | None = None,
    ) -> dict:
        normalized_username = username or None
        normalized_notes = [line.strip() for line in (notes or "").splitlines() if line.strip()]

        def mutate(payload: VaultPayload) -> dict[str, Any]:
            records = [dict(record) for record in payload.records]
            timestamp = _utc_now()
            target_key = existing_key or record_key
            found_index: int | None = None
            for index, record in enumerate(records):
                if record["key"] == target_key:
                    found_index = index
                    break

            if existing_key is None:
                if any(record["key"] == record_key for record in records):
                    raise ValueError("record key already exists, use update instead")
                records.append(
                    {
                        "key": record_key,
                        "name": name,
                        "username": normalized_username,
                        "secret": secret,
                        "notes": normalized_notes,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                )
            else:
                if found_index is None:
                    raise ValueError("record key not found")
                if record_key != existing_key and any(record["key"] == record_key for record in records):
                    raise ValueError("record key already exists, use update instead")
                original = records[found_index]
                next_secret = secret if secret else str(original["secret"])
                records[found_index] = {
                    **original,
                    "key": record_key,
                    "name": name,
                    "username": normalized_username,
                    "secret": next_secret,
                    "notes": normalized_notes,
                    "updated_at": timestamp,
                }

            payload.records.clear()
            payload.records.extend(records)
            data = payload.to_dict()
            data["vault"]["updated_at"] = timestamp
            return data

        return await self._save_payload_mutation(mutate)

    async def delete_record(self, record_key: str) -> dict:
        def mutate(payload: VaultPayload) -> dict[str, Any]:
            records = [dict(record) for record in payload.records]
            remaining = [record for record in records if record["key"] != record_key]
            if len(remaining) == len(records):
                raise ValueError("record key not found")
            payload.records.clear()
            payload.records.extend(remaining)
            data = payload.to_dict()
            data["vault"]["updated_at"] = _utc_now()
            return data

        return await self._save_payload_mutation(mutate)

    async def copy_record_secret(self, record_key: str) -> dict:
        try:
            return self._clipboard.prepare_secret_for_clipboard(record_key=record_key, caller="ui")
        except ValueError as exc:
            raise RuntimeError("record copy failed") from exc

    async def _save_payload_mutation(self, mutate) -> dict:
        try:
            payload_dict = self._auth.access_vault(pin=None, caller="ui", operation=mutate)
            payload = VaultPayload.from_dict(payload_dict)
            master_password = self._require_ui_master_password()
            self._auth.store.save_vault(payload, master_password=master_password)
            return await self.get_status()
        except AuthenticationError as exc:
            raise RuntimeError(str(exc)) from exc
        except AccessStateError as exc:
            raise RuntimeError("vault access requires an active unlocked session") from exc
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        except VaultBlobError as exc:
            raise RuntimeError("record save failed") from exc

    def _cache_ui_master_password(self, master_password: str) -> None:
        self._wipe_ui_master_password()
        self._ui_master_password = bytearray(master_password.encode("utf-8"))

    def _wipe_ui_master_password(self) -> None:
        if self._ui_master_password is not None:
            for index in range(len(self._ui_master_password)):
                self._ui_master_password[index] = 0
            self._ui_master_password = None

    def _require_ui_master_password(self) -> str:
        if self._ui_master_password is None:
            raise RuntimeError("write operations require a fresh master password unlock in this plugin session")
        return self._ui_master_password.decode("utf-8")

    async def _main(self):
        decky.logger.info("decky-secrets backend loaded")

    async def _unload(self):
        self._wipe_ui_master_password()
        decky.logger.info("decky-secrets backend unloaded")

    async def _uninstall(self):
        self._wipe_ui_master_password()
        decky.logger.info("decky-secrets backend uninstalled")
