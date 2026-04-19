from dataclasses import asdict, dataclass
from typing import Literal

import decky

from decky_secrets.vault import VAULT_FILE_NAME, VaultFileStore

VaultState = Literal[
    "uninitialized_vault",
    "decrypt_required",
    "session_locked",
    "accessible",
    "relocking",
]


@dataclass(frozen=True)
class RuntimeStatus:
    plugin: str
    version: str
    vault_state: VaultState
    backend_model: str
    notes: list[str]
    vault_path: str
    vault_exists: bool


class Plugin:
    def __init__(self) -> None:
        self._store = VaultFileStore()

    async def get_status(self) -> dict:
        vault_exists = self._store.vault_path.exists()
        status = RuntimeStatus(
            plugin="decky-secrets",
            version="0.0.2",
            vault_state="decrypt_required" if vault_exists else "uninitialized_vault",
            backend_model="python-vault-persistence",
            notes=[
                "Vault persistence and encrypted blob storage are now implemented in the Python backend.",
                "Master-password and PIN/session unlock state handling remain intentionally separate from this slice.",
                f"Vault file name is reserved as {VAULT_FILE_NAME} under ~/.decky-secrets/.",
            ],
            vault_path=str(self._store.vault_path),
            vault_exists=vault_exists,
        )
        return asdict(status)

    async def _main(self):
        decky.logger.info("decky-secrets backend loaded")

    async def _unload(self):
        decky.logger.info("decky-secrets backend unloaded")

    async def _uninstall(self):
        decky.logger.info("decky-secrets backend uninstalled")
