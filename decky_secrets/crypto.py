from __future__ import annotations

from Cryptodome.Cipher import AES

AES_GCM_TAG_SIZE = 16


class AuthTagError(Exception):
    pass


def encrypt_aes_gcm(*, key: bytes | bytearray, nonce: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(bytes(key), AES.MODE_GCM, nonce=nonce, mac_len=AES_GCM_TAG_SIZE)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return ciphertext + tag


def decrypt_aes_gcm(*, key: bytes | bytearray, nonce: bytes, ciphertext_and_tag: bytes) -> bytes:
    if len(ciphertext_and_tag) < AES_GCM_TAG_SIZE:
        raise AuthTagError("ciphertext is too short")
    ciphertext = ciphertext_and_tag[:-AES_GCM_TAG_SIZE]
    tag = ciphertext_and_tag[-AES_GCM_TAG_SIZE:]
    cipher = AES.new(bytes(key), AES.MODE_GCM, nonce=nonce, mac_len=AES_GCM_TAG_SIZE)
    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as exc:
        raise AuthTagError("authentication tag verification failed") from exc
