# Decision: Vault security baseline for MVP

- Status: accepted
- Date: 2026-04-18
- Owner: Spec

## Context
The project needed a concrete vault security baseline before implementation work could be made ready. Earlier project docs intentionally left the crypto profile, in-memory handling model, PIN behavior, recovery flow, and authentication-failure policy open.

## Decision
The MVP vault security baseline is:

1. **Vault at rest**
   - Store the vault as a single versioned encrypted blob at `~/.decky-secrets/vault`.
   - Encrypt with **AES-256-GCM**.
   - Use Python `hashlib.pbkdf2_hmac` for PBKDF2-SHA-256 derivation.
   - Use the Python `cryptography` library for AES-GCM operations.
   - Use Python `secrets` for random salt, nonce, and recovery-key generation.
   - Derive the master-password key with **PBKDF2-SHA-256**, **600,000 iterations**, and a random salt.
   - Use a fresh standard **96-bit AES-GCM nonce** for each encryption operation.
   - Recommended default salt size is 16 bytes.
   - Recommended blob shape is a minimal header with version, KDF metadata, nonce, and ciphertext, with secret-bearing data inside the encrypted payload.
   - Best-guess payload structure: vault timestamps, PIN value and KDF metadata, and a record array where each record has `key`, `name`, optional `username`, `secret`, `notes`, and timestamps.

2. **In-memory handling**
   - The Python backend owns all cryptographic enforcement.
   - After master-password unlock, the whole vault is re-wrapped into **PIN-encrypted memory**.
   - The vault remains encrypted in memory at all times except during the shortest practical active operation window.
   - Active plaintext use decrypts the whole vault briefly for the operation, then re-encrypts it in memory immediately.
   - Plaintext memory must be zeroed after use.
   - The implementation should avoid swap/pagefile exposure where practical.
   - This is a hardened best-effort memory model, not an absolute guarantee against a privileged local attacker.

3. **PIN policy**
   - PIN is **required** for session access after password unlock.
   - PINs are **numeric only**, **4 to 6 digits**.
   - Derive the PIN key with **PBKDF2-SHA-256**, **200,000 iterations**, and a separate random salt.
   - The PIN value is stored inside the master vault and exposed only transiently in the backend when needed to perform in-memory re-encryption or decryption.
   - The default session access window is **1 minute** since last vault access, after which the vault returns to PIN-encrypted in-memory state.
   - Full relock is a separate configurable timeout with a default of **6 hours**.

4. **Recovery and credential changes**
   - Generate a **32-character base32 recovery key** grouped for readability, for example `ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ12-3456`.
   - The recovery key is shown to the user to store separately and is **not stored on the device**.
   - Master-password changes require either the current password or the recovery key.
   - PIN changes require the master password.

5. **Frontend, CLI, and clipboard behavior**
   - The frontend may receive decrypted private values only for explicit viewing or copy-to-clipboard actions.
   - A local CLI tool may add, list, remove, and update secrets directly in the same vault for shell and SSH-based workflows.
   - The CLI uses the same vault format, backend validation rules, and lock requirements as the UI path.
   - MVP CLI commands are `add`, `list`, `rm`, and `update`.
   - Secret input should work via `--secret` or `--secret-stdin`.
   - `--username` may be supported where relevant.
   - If the vault is fully locked, the CLI should prompt for the master password using non-echo terminal input.
   - If the vault is session-locked, the CLI should prompt for the PIN using non-echo terminal input.
   - If `--secret-stdin` is in use, prompts should read from `/dev/tty` when available.
   - If secure prompting is not possible, the CLI should fail cleanly rather than consume piped secret input or echo secrets.
   - Secret values remain masked by default in the UI.
   - Reveal and copy actions require explicit user intent.
   - Clipboard auto-clear is required and defaults to **30 seconds**.

6. **Authentication-failure handling**
   - Password, PIN, and recovery-key failures count toward the same combined counters.
   - Default rate limits are **5 failed attempts per minute** and **20 failed attempts per 10 minutes**.
   - Delete-on-failure is configurable, clearly warned, and **off by default**.
   - If enabled, the default destructive threshold is **40 combined authentication failures**.

## Rationale
- AES-256-GCM plus explicit PBKDF2 settings gives the MVP a concrete and reviewable cryptographic baseline.
- Keeping the vault PIN-encrypted in memory addresses the stated product requirement to avoid long-lived plaintext process memory between accesses.
- Making the PIN required simplifies the security model and avoids an optional branch that would otherwise leave plaintext in memory.
- Recovery must exist for password changes, but storing the recovery key on-device would undercut its purpose.
- A CLI path supports technical users who need to move large or complex secrets over SSH without broadening the storage or trust model.
- `--secret-stdin` reduces shell-history and quoting problems for CLI secret entry.
- Interactive `/dev/tty` prompting is the safest best-guess CLI auth behavior for MVP shell and SSH use.
- Failure throttling should be on by default, while destructive deletion should be opt-in to avoid surprising users.

## Consequences
- Product docs must now describe the PIN as required for session access, not optional.
- Implementation planning must include whole-vault in-memory re-wrap behavior and memory zeroization.
- UI work must show masked-by-default secrets, explicit reveal/copy controls, and a warninged opt-in destructive-failure option.
- Implementation planning must include a CLI path that uses the same backend and vault semantics as the UI.
- Builder readiness still depends on validating the best-guess schema and deciding whether any non-interactive CLI auth path is needed.

## Rejected alternative
- **Optional PIN with potentially persistent plaintext in memory:** rejected because the requirement set prioritized keeping the vault encrypted in memory at rest within the running session.
