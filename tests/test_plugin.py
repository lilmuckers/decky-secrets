from __future__ import annotations

import asyncio
import sys
import tempfile
import types
import unittest
from pathlib import Path

from decky_secrets import AuthConfig, ClipboardCopyService, VaultAuthManager, VaultFileStore


decky_stub = types.SimpleNamespace(logger=types.SimpleNamespace(info=lambda *args, **kwargs: None))
sys.modules.setdefault("decky", decky_stub)

from main import Plugin  # noqa: E402


class PluginUiFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = VaultFileStore(home_dir=Path(self.temp_dir.name))
        self.auth = VaultAuthManager(
            store=self.store,
            config=AuthConfig(short_window_attempt_limit=3, short_window_seconds=30),
        )
        self.plugin = Plugin(auth=self.auth, clipboard=ClipboardCopyService(auth=self.auth, clipboard_clear_seconds=30))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_vault_unlocks_and_reports_pin_length(self) -> None:
        status = asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))

        self.assertEqual(status["state"], "accessible")
        runtime = asyncio.run(self.plugin.get_status())
        self.assertEqual(runtime["vault_state"], "accessible")
        self.assertEqual(runtime["session_pin_length"], 4)

    def test_list_and_detail_paths_keep_routine_payloads_non_secret(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "hunter2", "2FA backup", None))

        records = asyncio.run(self.plugin.list_records())
        detail = asyncio.run(self.plugin.get_record_detail("battle-net"))

        self.assertEqual(records, [{"key": "battle-net", "name": "Battle.net", "username": "player123"}])
        self.assertNotIn("secret", detail)
        self.assertEqual(detail["notes"], "2FA backup")

    def test_reveal_and_copy_are_explicit_secret_bearing_actions(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "hunter2", "", None))

        reveal = asyncio.run(self.plugin.reveal_record_secret("battle-net"))
        copy_payload = asyncio.run(self.plugin.copy_record_secret("battle-net"))

        self.assertEqual(reveal["secret"], "hunter2")
        self.assertEqual(copy_payload["secret"], "hunter2")
        self.assertEqual(copy_payload["record_name"], "Battle.net")

    def test_lock_to_pin_blocks_secret_bearing_actions_until_pin_unlock(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "hunter2", "", None))
        asyncio.run(self.plugin.lock_to_pin())

        with self.assertRaisesRegex(RuntimeError, "vault access requires an active unlocked session"):
            asyncio.run(self.plugin.list_records())

        unlocked = asyncio.run(self.plugin.unlock_with_pin("1234"))

        self.assertEqual(unlocked["state"], "accessible")
        records = asyncio.run(self.plugin.list_records())
        self.assertEqual(len(records), 1)

    def test_pin_failure_feedback_and_lockout_stay_generic(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.lock_to_pin())

        with self.assertRaisesRegex(RuntimeError, "PIN unlock failed"):
            asyncio.run(self.plugin.unlock_with_pin("9999"))
        with self.assertRaisesRegex(RuntimeError, "PIN unlock failed"):
            asyncio.run(self.plugin.unlock_with_pin("9999"))
        with self.assertRaisesRegex(RuntimeError, "PIN unlock failed"):
            asyncio.run(self.plugin.unlock_with_pin("9999"))

        with self.assertRaisesRegex(RuntimeError, "authentication temporarily blocked"):
            asyncio.run(self.plugin.unlock_with_pin("1234"))

    def test_add_edit_and_delete_flows_use_backend_validation(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "hunter2", "old note", None))

        with self.assertRaisesRegex(RuntimeError, "record key already exists, use update instead"):
            asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "new-secret", "dup", None))

        asyncio.run(
            self.plugin.save_record(
                "battle-net-renamed",
                "Battle.net",
                "new-player",
                "new-secret",
                "new note",
                "battle-net",
            )
        )
        detail = asyncio.run(self.plugin.get_record_detail("battle-net-renamed"))
        self.assertEqual(detail["username"], "new-player")
        self.assertEqual(detail["notes"], "new note")

        asyncio.run(self.plugin.delete_record("battle-net-renamed"))
        self.assertEqual(asyncio.run(self.plugin.list_records()), [])

    def test_write_operations_require_fresh_master_password_after_full_lock(self) -> None:
        asyncio.run(self.plugin.create_vault("correct horse battery staple", "1234"))
        asyncio.run(self.plugin.full_lock())
        asyncio.run(self.plugin.unlock_with_master_password("correct horse battery staple"))
        asyncio.run(self.plugin.unlock_with_pin("1234"))
        asyncio.run(self.plugin.save_record("battle-net", "Battle.net", "player123", "hunter2", "", None))
        asyncio.run(self.plugin.full_lock())
        asyncio.run(self.plugin.unlock_with_master_password("correct horse battery staple"))
        asyncio.run(self.plugin.unlock_with_pin("1234"))

        asyncio.run(self.plugin.save_record("battle-net-2", "Battle.net 2", "player456", "hunter3", "", None))
        records = asyncio.run(self.plugin.list_records())
        self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()
