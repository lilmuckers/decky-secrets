import os
import tempfile
import unittest
from pathlib import Path

from decky_secrets.auth import AccessStateError, VaultAuthManager
from decky_secrets.clipboard import (
    BEST_EFFORT_CLEAR_DISCLAIMER,
    DEFAULT_CLIPBOARD_CLEAR_SECONDS,
    ClipboardCopyService,
    resolve_clipboard_clear_seconds,
)
from decky_secrets.vault import VaultFileStore


class ClipboardCopyServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.store = VaultFileStore(home_dir=self.home)
        self.store.create_vault(
            master_password="correct horse battery staple",
            pin="1234",
            records=[
                {
                    "key": "battle-net",
                    "name": "Battle.net",
                    "username": "player123",
                    "secret": "super-secret-password",
                    "notes": ["2FA enabled"],
                }
            ],
        )
        self.auth = VaultAuthManager(store=self.store)
        self.service = ClipboardCopyService(auth=self.auth)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("DECKY_SECRETS_CLIPBOARD_CLEAR_SECONDS", None)

    def _unlock(self) -> None:
        self.auth.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.auth.unlock_with_pin(pin="1234", caller="ui")

    def test_default_timeout_is_30_seconds(self) -> None:
        os.environ.pop("DECKY_SECRETS_CLIPBOARD_CLEAR_SECONDS", None)
        self.assertEqual(resolve_clipboard_clear_seconds(), DEFAULT_CLIPBOARD_CLEAR_SECONDS)

    def test_custom_timeout_can_be_configured(self) -> None:
        os.environ["DECKY_SECRETS_CLIPBOARD_CLEAR_SECONDS"] = "45"
        self.assertEqual(resolve_clipboard_clear_seconds(), 45)

    def test_list_and_copy_require_accessible_state(self) -> None:
        with self.assertRaises(AccessStateError):
            self.service.list_records(caller="ui")

        with self.assertRaises(AccessStateError):
            self.service.prepare_secret_for_clipboard(record_key="battle-net", caller="ui")

    def test_copy_returns_secret_only_for_explicit_copy_request(self) -> None:
        self._unlock()

        records = self.service.list_records(caller="ui")
        self.assertEqual(
            records,
            [
                {
                    "key": "battle-net",
                    "name": "Battle.net",
                    "username": "player123",
                }
            ],
        )

        payload = self.service.prepare_secret_for_clipboard(record_key="battle-net", caller="ui")
        self.assertEqual(payload["record_key"], "battle-net")
        self.assertEqual(payload["record_name"], "Battle.net")
        self.assertEqual(payload["secret"], "super-secret-password")
        self.assertEqual(payload["clipboard_clear_seconds"], DEFAULT_CLIPBOARD_CLEAR_SECONDS)
        self.assertTrue(payload["best_effort_clear"])
        self.assertEqual(payload["clear_disclaimer"], BEST_EFFORT_CLEAR_DISCLAIMER)

    def test_copy_unknown_record_raises_without_echoing_secrets(self) -> None:
        self._unlock()

        with self.assertRaises(ValueError) as exc:
            self.service.prepare_secret_for_clipboard(record_key="missing", caller="ui")

        self.assertEqual(str(exc.exception), "record not found")
        self.assertNotIn("super-secret-password", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
