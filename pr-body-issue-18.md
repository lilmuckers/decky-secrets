## Summary
- replace the failing Steam Deck `cryptography` AES-GCM runtime path with a `pycryptodomex`-backed AES-256-GCM helper so the backend keeps the approved AES-256-GCM + PBKDF2-SHA-256 posture without the OpenSSL ABI dependency that failed on device
- keep the existing vault blob format and auth/session model intact by preserving the same 32-byte keys, 12-byte nonce contract, and combined ciphertext-plus-tag storage shape
- document the chosen Steam Deck compatible runtime strategy in README and the durable architecture/decision mirrors

## Testing
- `python3 -m unittest tests.test_crypto tests.test_import_layout tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli tests.test_plugin` (validated locally using an unpacked `pycryptodomex` wheel on the repo import path because the sandbox Python is externally managed)
- `python3 -m py_compile main.py decky_secrets/crypto.py decky_secrets/vault.py decky_secrets/auth.py decky_secrets/clipboard.py decky_secrets/cli.py decky_secrets/__main__.py`
- `node --test tests/clipboard-flow.test.mjs tests/ui-flow.test.mjs tests/ui-contract.test.mjs`
- `corepack pnpm build`
- inspected `pycryptodomex` wheel linkage locally with `ldd` on `Cryptodome/Cipher/_raw_aes.abi3.so`; the observed dependency set was `libpthread`, `libc`, and the dynamic loader, with no `libcrypto.so.3` dependency in that module

## Scope notes
- this keeps issue #17's import-layout fix separate and unchanged
- this does not weaken the AES-256-GCM or PBKDF2-SHA-256 baseline
- real Steam Deck validation is still required for acceptance and could not be completed from this workspace because no paired Deck/hardware access was available here
