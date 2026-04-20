from dataclasses import asdict, dataclass

import decky

from decky_secrets.auth import VaultAuthManager, VaultState
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


class Plugin:
    def __init__(self) -> None:
        self._auth = VaultAuthManager()

    async def get_status(self) -> dict:
        auth_status = self._auth.get_status()
        status = RuntimeStatus(
            plugin="decky-secrets",
            version="0.0.3",
            vault_state=auth_status.state,
            backend_model="python-auth-backend",
            notes=[
                "Vault persistence, lock-state handling, and authentication throttling now live in the Python backend.",
                "Restart and full-relock paths require the master password again by design.",
                f"Vault file name is reserved as {VAULT_FILE_NAME} under ~/.decky-secrets/.",
            ],
            vault_path=str(self._auth.store.vault_path),
            vault_exists=auth_status.vault_exists,
            auth_locked_until=auth_status.auth_locked_until,
            session_access_expires_at=auth_status.session_access_expires_at,
            full_relock_at=auth_status.full_relock_at,
        )
        return asdict(status)

    async def _main(self):
        decky.logger.info("decky-secrets backend loaded")

    async def _unload(self):
        decky.logger.info("decky-secrets backend unloaded")

    async def _uninstall(self):
        decky.logger.info("decky-secrets backend uninstalled")
