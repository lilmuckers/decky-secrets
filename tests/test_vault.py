import base64
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from decky_secrets.vault import (
    CURRENT_BLOB_VERSION,
    CURRENT_KDF_ALGORITHM,
    CURRENT_KDF_ITERATIONS,
    CURRENT_PIN_KDF_ITERATIONS,
    VaultBlobError,
    VaultFileStore,
    VaultPayload,
    VaultPayloadPin,
    VaultPayloadVault,
    create_recovery_key,
)


class VaultFileStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.home = Path(self.temp_dir.name)
        self.store = VaultFileStore(home_dir=self.home)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_and_load_round_trip(self) -> None:
        payload = self.store.create_vault(master_password="correct horse battery staple", pin="1234")

        self.assertEqual(payload.vault.version, CURRENT_BLOB_VERSION)
        self.assertTrue(self.store.vault_path.exists())

        loaded = self.store.load_vault(master_password="correct horse battery staple")
        self.assertEqual(loaded.to_dict(), payload.to_dict())

    def test_blob_header_uses_expected_cleartext_shape_without_secret_values(self) -> None:
        payload = VaultPayload(
            vault=VaultPayloadVault(created_at="2026-04-19T20:00:00Z", updated_at="2026-04-19T20:00:00Z"),
            pin=VaultPayloadPin(
                value="123456",
                kdf={
                    "algorithm": CURRENT_KDF_ALGORITHM,
                    "iterations": CURRENT_PIN_KDF_ITERATIONS,
                    "salt_b64": base64.b64encode(b"1" * 16).decode("ascii"),
                },
            ),
            records=[
                {
                    "key": "launcher",
                    "name": "Launcher",
                    "username": "patrick",
                    "secret": "super-secret-value",
                    "notes": ["note one"],
                    "created_at": "2026-04-19T20:00:00Z",
                    "updated_at": "2026-04-19T20:00:00Z",
                }
            ],
        )

        self.store.save_vault(payload, master_password="correct horse battery staple")

        raw_text = self.store.vault_path.read_text(encoding="utf-8")
        self.assertNotIn("super-secret-value", raw_text)
        self.assertNotIn('"123456"', raw_text)

        blob = json.loads(raw_text)
        self.assertEqual(blob["magic"], "DSV1")
        self.assertEqual(blob["version"], CURRENT_BLOB_VERSION)
        self.assertEqual(blob["kdf"]["algorithm"], CURRENT_KDF_ALGORITHM)
        self.assertEqual(blob["kdf"]["iterations"], CURRENT_KDF_ITERATIONS)
        self.assertEqual(blob["cipher"]["algorithm"], "aes-256-gcm")
        self.assertIn("ciphertext_b64", blob)

    def test_restrictive_permissions_are_applied(self) -> None:
        self.store.create_vault(master_password="correct horse battery staple", pin="1234")

        dir_mode = stat.S_IMODE(os.stat(self.store.vault_dir).st_mode)
        file_mode = stat.S_IMODE(os.stat(self.store.vault_path).st_mode)

        self.assertEqual(dir_mode, 0o700)
        self.assertEqual(file_mode, 0o600)

    def test_invalid_password_fails_without_leaking_payload(self) -> None:
        self.store.create_vault(master_password="correct horse battery staple", pin="1234")

        with self.assertRaises(VaultBlobError):
            self.store.load_vault(master_password="wrong password")

    def test_duplicate_record_keys_are_rejected(self) -> None:
        payload = VaultPayload(
            vault=VaultPayloadVault(created_at="2026-04-19T20:00:00Z", updated_at="2026-04-19T20:00:00Z"),
            pin=VaultPayloadPin(
                value="123456",
                kdf={
                    "algorithm": CURRENT_KDF_ALGORITHM,
                    "iterations": CURRENT_PIN_KDF_ITERATIONS,
                    "salt_b64": base64.b64encode(b"1" * 16).decode("ascii"),
                },
            ),
            records=[
                {
                    "key": "launcher",
                    "name": "Launcher",
                    "username": None,
                    "secret": "secret-one",
                    "notes": [],
                    "created_at": "2026-04-19T20:00:00Z",
                    "updated_at": "2026-04-19T20:00:00Z",
                },
                {
                    "key": "launcher",
                    "name": "Launcher 2",
                    "username": None,
                    "secret": "secret-two",
                    "notes": [],
                    "created_at": "2026-04-19T20:00:00Z",
                    "updated_at": "2026-04-19T20:00:00Z",
                },
            ],
        )

        with self.assertRaises(VaultBlobError):
            self.store.save_vault(payload, master_password="correct horse battery staple")

    def test_recovery_key_shape(self) -> None:
        recovery_key = create_recovery_key()
        parts = recovery_key.split("-")
        self.assertEqual(len(parts), 8)
        self.assertTrue(all(len(part) == 4 for part in parts))


if __name__ == "__main__":
    unittest.main()
