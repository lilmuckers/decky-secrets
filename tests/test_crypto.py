from __future__ import annotations

import unittest

from decky_secrets.crypto import AuthTagError, decrypt_aes_gcm, encrypt_aes_gcm


class CryptoTests(unittest.TestCase):
    def test_encrypt_decrypt_round_trip(self) -> None:
        key = b"k" * 32
        nonce = b"n" * 12
        plaintext = b"vault-payload"

        ciphertext = encrypt_aes_gcm(key=key, nonce=nonce, plaintext=plaintext)

        self.assertNotEqual(ciphertext, plaintext)
        self.assertEqual(decrypt_aes_gcm(key=key, nonce=nonce, ciphertext_and_tag=ciphertext), plaintext)

    def test_decrypt_rejects_tampered_ciphertext(self) -> None:
        key = b"k" * 32
        nonce = b"n" * 12
        plaintext = b"vault-payload"

        ciphertext = bytearray(encrypt_aes_gcm(key=key, nonce=nonce, plaintext=plaintext))
        ciphertext[-1] ^= 0x01

        with self.assertRaises(AuthTagError):
            decrypt_aes_gcm(key=key, nonce=nonce, ciphertext_and_tag=bytes(ciphertext))


if __name__ == "__main__":
    unittest.main()
