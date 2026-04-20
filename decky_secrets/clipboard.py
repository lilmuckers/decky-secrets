from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .auth import CallerType, VaultAuthManager

DEFAULT_CLIPBOARD_CLEAR_SECONDS = 30
MIN_CLIPBOARD_CLEAR_SECONDS = 5
MAX_CLIPBOARD_CLEAR_SECONDS = 300
CLIPBOARD_TIMEOUT_ENV_VAR = "DECKY_SECRETS_CLIPBOARD_CLEAR_SECONDS"
BEST_EFFORT_CLEAR_DISCLAIMER = (
    "Clipboard clear is best effort only. It may not remove values from clipboard history, already pasted destinations, or crash/restart scenarios."
)


@dataclass(frozen=True)
class RecordSummary:
    key: str
    name: str
    username: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "key": self.key,
            "name": self.name,
            "username": self.username,
        }


@dataclass(frozen=True)
class ClipboardCopyPayload:
    record_key: str
    record_name: str
    secret: str
    clipboard_clear_seconds: int
    best_effort_clear: bool = True
    clear_disclaimer: str = BEST_EFFORT_CLEAR_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_key": self.record_key,
            "record_name": self.record_name,
            "secret": self.secret,
            "clipboard_clear_seconds": self.clipboard_clear_seconds,
            "best_effort_clear": self.best_effort_clear,
            "clear_disclaimer": self.clear_disclaimer,
        }


class ClipboardCopyService:
    def __init__(self, *, auth: VaultAuthManager, clipboard_clear_seconds: int | None = None) -> None:
        self.auth = auth
        self.clipboard_clear_seconds = resolve_clipboard_clear_seconds(clipboard_clear_seconds)

    def list_records(self, *, caller: CallerType = "ui") -> list[dict[str, str | None]]:
        return self.auth.access_vault(
            pin=None,
            caller=caller,
            operation=lambda payload: [
                RecordSummary(
                    key=str(record["key"]),
                    name=str(record["name"]),
                    username=record.get("username") if isinstance(record.get("username"), str) else None,
                ).to_dict()
                for record in payload.records
            ],
        )

    def prepare_secret_for_clipboard(self, *, record_key: str, caller: CallerType = "ui") -> dict[str, Any]:
        def operation(payload: Any) -> dict[str, Any]:
            for record in payload.records:
                if record.get("key") == record_key:
                    return ClipboardCopyPayload(
                        record_key=record_key,
                        record_name=str(record["name"]),
                        secret=str(record["secret"]),
                        clipboard_clear_seconds=self.clipboard_clear_seconds,
                    ).to_dict()
            raise ValueError("record not found")

        return self.auth.access_vault(pin=None, caller=caller, operation=operation)


def resolve_clipboard_clear_seconds(value: int | None = None) -> int:
    candidate = value
    if candidate is None:
        raw = os.environ.get(CLIPBOARD_TIMEOUT_ENV_VAR)
        if raw is None or raw == "":
            candidate = DEFAULT_CLIPBOARD_CLEAR_SECONDS
        else:
            try:
                candidate = int(raw)
            except ValueError as exc:
                raise ValueError("clipboard clear timeout must be an integer") from exc

    if not isinstance(candidate, int):
        raise ValueError("clipboard clear timeout must be an integer")
    if candidate < MIN_CLIPBOARD_CLEAR_SECONDS or candidate > MAX_CLIPBOARD_CLEAR_SECONDS:
        raise ValueError(
            f"clipboard clear timeout must be between {MIN_CLIPBOARD_CLEAR_SECONDS} and {MAX_CLIPBOARD_CLEAR_SECONDS} seconds"
        )
    return candidate
