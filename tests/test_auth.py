import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from decky_secrets.auth import (
    DEFAULT_FULL_RELOCK_TIMEOUT_SECONDS,
    DEFAULT_SESSION_ACCESS_WINDOW_SECONDS,
    AccessStateError,
    AuthConfig,
    AuthenticationError,
    AuthenticationLockedError,
    VaultAuthManager,
)
from decky_secrets.vault import VaultFileStore


class FakeClock:
    def __init__(self, start: datetime | None = None) -> None:
        self.current = start or datetime(2026, 4, 20, 7, 0, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.current

    def advance(self, *, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


class VaultAuthManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.store = VaultFileStore(home_dir=self.home)
        self.clock = FakeClock()
        self.manager = VaultAuthManager(store=self.store, clock=self.clock)
        self.store.create_vault(master_password="correct horse battery staple", pin="1234")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_password_unlock_then_pin_unlock_then_session_timeout(self) -> None:
        status = self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.assertEqual(status.state, "session_locked")

        status = self.manager.unlock_with_pin(pin="1234", caller="ui")
        self.assertEqual(status.state, "accessible")

        record_count = self.manager.access_vault(
            pin=None,
            caller="ui",
            operation=lambda payload: len(payload.records),
        )
        self.assertEqual(record_count, 0)

        self.clock.advance(seconds=DEFAULT_SESSION_ACCESS_WINDOW_SECONDS + 1)
        status = self.manager.get_status()
        self.assertEqual(status.state, "session_locked")

        with self.assertRaises(AccessStateError):
            self.manager.access_vault(pin=None, caller="ui", operation=lambda payload: payload.records)

    def test_full_relock_requires_master_password_again(self) -> None:
        self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.manager.unlock_with_pin(pin="1234", caller="ui")

        self.clock.advance(seconds=DEFAULT_FULL_RELOCK_TIMEOUT_SECONDS + 1)
        status = self.manager.get_status()
        self.assertEqual(status.state, "decrypt_required")

        with self.assertRaises(AccessStateError):
            self.manager.unlock_with_pin(pin="1234", caller="ui")

    def test_restart_starts_fully_locked(self) -> None:
        self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.manager.unlock_with_pin(pin="1234", caller="ui")

        restarted = VaultAuthManager(store=self.store, clock=self.clock)
        self.assertEqual(restarted.get_status().state, "decrypt_required")

        with self.assertRaises(AccessStateError):
            restarted.unlock_with_pin(pin="1234", caller="ui")

    def test_shared_throttling_applies_across_factors_and_callers(self) -> None:
        for _ in range(4):
            with self.assertRaises(AuthenticationError):
                self.manager.unlock_with_password(master_password="wrong password", caller="ui")

        with self.assertRaises(AuthenticationError):
            self.manager.authenticate_recovery_key(
                provided_recovery_key="WRONG-WRONG-WRONG-WRONG-WRONG-WRONG-WRONG-WRONG",
                expected_recovery_key="ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ23-4567",
                caller="cli",
            )

        with self.assertRaises(AuthenticationLockedError):
            self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")

        self.clock.advance(seconds=61)
        status = self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.assertEqual(status.state, "session_locked")

    def test_delete_on_failure_can_destroy_vault_after_combined_failures(self) -> None:
        destructive = VaultAuthManager(
            store=self.store,
            clock=self.clock,
            config=replace(AuthConfig(), delete_on_failure=True, delete_on_failure_threshold=3),
        )

        with self.assertRaises(AuthenticationError):
            destructive.unlock_with_password(master_password="wrong password", caller="cli")

        destructive.unlock_with_password(master_password="correct horse battery staple", caller="cli")
        destructive.unlock_with_pin(pin="1234", caller="cli")

        with self.assertRaises(AuthenticationError):
            destructive.authenticate_recovery_key(
                provided_recovery_key="WRONG-WRONG-WRONG-WRONG-WRONG-WRONG-WRONG-WRONG",
                expected_recovery_key="ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ23-4567",
                caller="cli",
            )

        with self.assertRaises(AuthenticationError):
            destructive.unlock_with_password(master_password="wrong password", caller="cli")

        self.assertFalse(self.store.vault_path.exists())
        self.assertEqual(destructive.get_status().state, "uninitialized_vault")

    def test_accessible_window_does_not_require_pin_resubmission(self) -> None:
        self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        self.manager.unlock_with_pin(pin="1234", caller="ui")

        result = self.manager.access_vault(
            pin=None,
            caller="ui",
            operation=lambda payload: payload.vault.version,
        )

        self.assertEqual(result, 1)
        self.assertEqual(self.manager.get_status().state, "accessible")

    def test_error_messages_do_not_echo_secrets(self) -> None:
        bad_password = "wrong-password-secret"
        bad_pin = "9999"

        with self.assertRaises(AuthenticationError) as password_error:
            self.manager.unlock_with_password(master_password=bad_password, caller="ui")
        self.assertNotIn(bad_password, str(password_error.exception))

        self.manager.unlock_with_password(master_password="correct horse battery staple", caller="ui")
        with self.assertRaises(AuthenticationError) as pin_error:
            self.manager.unlock_with_pin(pin=bad_pin, caller="ui")
        self.assertNotIn(bad_pin, str(pin_error.exception))


if __name__ == "__main__":
    unittest.main()
