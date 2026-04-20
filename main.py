from dataclasses import asdict, dataclass

import decky

from decky_secrets import BEST_EFFORT_CLEAR_DISCLAIMER, ClipboardCopyService, VaultAuthManager, VaultState
from decky_secrets.vault import VAULT_FILE_NAME


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
    clipboard_clear_seconds: int
    clipboard_clear_best_effort: bool
    clipboard_clear_disclaimer: str


class Plugin:
    def __init__(self) -> None:
        self._auth = VaultAuthManager()
        self._clipboard = ClipboardCopyService(auth=self._auth)

    async def get_status(self) -> dict:
        auth_status = self._auth.get_status()
        status = RuntimeStatus(
            plugin="decky-secrets",
            version="0.0.4",
            vault_state=auth_status.state,
            backend_model="python-auth-backend",
            notes=[
                "Password copy is an explicit UI action and clipboard clearing is best effort only.",
                "Fresh copy actions stay behind the shared backend auth boundary and stop when the session relocks.",
                f"Vault file name is reserved as {VAULT_FILE_NAME} under ~/.decky-secrets/.",
            ],
            vault_path=str(self._auth.store.vault_path),
            vault_exists=auth_status.vault_exists,
            auth_locked_until=auth_status.auth_locked_until,
            session_access_expires_at=auth_status.session_access_expires_at,
            full_relock_at=auth_status.full_relock_at,
            clipboard_clear_seconds=self._clipboard.clipboard_clear_seconds,
            clipboard_clear_best_effort=True,
            clipboard_clear_disclaimer=BEST_EFFORT_CLEAR_DISCLAIMER,
        )
        return asdict(status)

    async def list_records(self) -> list[dict]:
        return self._clipboard.list_records(caller="ui")

    async def copy_record_secret(self, record_key: str) -> dict:
        try:
            return self._clipboard.prepare_secret_for_clipboard(record_key=record_key, caller="ui")
        except ValueError as exc:
            raise RuntimeError("record copy failed") from exc

    async def _main(self):
        decky.logger.info("decky-secrets backend loaded")

    async def _unload(self):
        decky.logger.info("decky-secrets backend unloaded")

    async def _uninstall(self):
        decky.logger.info("decky-secrets backend uninstalled")
