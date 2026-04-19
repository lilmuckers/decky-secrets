from dataclasses import asdict, dataclass
from typing import Literal

import decky

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


class Plugin:
    def __init__(self) -> None:
        self._status = RuntimeStatus(
            plugin="decky-secrets",
            version="0.0.1",
            vault_state="uninitialized_vault",
            backend_model="python-backend-placeholder",
            notes=[
                "Scaffold only. No vault persistence or cryptography is active yet.",
                "Reserved for full-lock versus session-lock state handling in later issues.",
                "Frontend currently renders placeholder Decky panels only.",
            ],
        )

    async def get_status(self) -> dict:
        return asdict(self._status)

    async def _main(self):
        decky.logger.info("decky-secrets scaffold loaded")

    async def _unload(self):
        decky.logger.info("decky-secrets scaffold unloaded")

    async def _uninstall(self):
        decky.logger.info("decky-secrets scaffold uninstalled")
