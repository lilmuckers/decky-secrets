# Architecture

## Purpose

`decky-secrets` is a Decky Loader plugin for Steam Deck / SteamOS that provides fast local access to game-related credentials without turning the device into a general-purpose cloud password manager.

The MVP architecture must prioritize two things at once:
- strong encrypted-at-rest protection for the vault
- low-friction retrieval of a password during a live gaming session

## MVP architecture summary

### Storage location
- The vault is stored locally at `~/.decky-secrets/vault`.
- No secret material is intentionally sent off-device.
- The directory should be created with restrictive permissions.

### Vault content model
Each vault record stores:
- record name
- username
- password
- multiple notes

The vault is expected to support multiple records.

### Input surfaces
The MVP supports two user-facing ways to manage secrets:
- the Decky plugin UI for normal handheld entry and management
- a local CLI tool for adding, listing, removing, and updating secrets directly in the same vault, primarily for technical users who want to work over shell or SSH

The CLI is an additional local-management surface, not a separate storage path or alternate trust model.

### Encryption model
- The vault must be cryptographically protected at rest as a single versioned encrypted blob with minimal cleartext metadata.
- Use **AES-256-GCM** for vault encryption.
- Use Python `hashlib.pbkdf2_hmac` for PBKDF2-SHA-256 key derivation.
- Use the Python `cryptography` library for AES-256-GCM operations.
- Use Python `secrets` for random salt, nonce, and recovery-key generation.
- Derive the master-password key with **PBKDF2-SHA-256** at **600,000 iterations** and a separate random salt.
- Use a fresh standard **96-bit AES-GCM nonce** for each encryption operation.
- A password is required to decrypt the vault on first unlock after boot.
- A password is also required again after the vault has fully re-locked following a configurable inactivity timeout.
- The password-based unlock path is the root decrypt capability for the MVP.
- Recommended blob shape: a small header with version, KDF metadata, nonce, and ciphertext, with secret-bearing data kept inside the encrypted payload.

### Best-guess vault blob schema
A good MVP best-guess schema is:

Cleartext header:
- `magic`: fixed format marker, for example `DSV1`
- `version`: integer format version, initially `1`
- `kdf`: `{ algorithm, iterations, salt_b64 }`
- `cipher`: `{ algorithm, nonce_b64 }`
- `ciphertext_b64`: encrypted payload including GCM authentication tag

Encrypted payload:
- `vault`: `{ created_at, updated_at }`
- `pin`: `{ value, kdf: { algorithm, iterations, salt_b64 } }`
- `records`: array of objects shaped like:
  - `key`: stable unique record identifier used by the CLI
  - `name`: user-facing display name
  - `username`: optional username
  - `secret`: the stored password or secret value
  - `notes`: string array
  - `created_at`: timestamp
  - `updated_at`: timestamp
- `settings`: secret-sensitive internal values only when they truly need to live inside the encrypted payload

Best-guess defaults:
- store salts, nonces, and ciphertext using base64 encoding in the serialized format
- store timestamps as UTC ISO-8601 strings
- use `key` as the canonical CLI identifier and require uniqueness within the vault
- keep non-secret UX configuration outside the encrypted payload unless it materially affects security behavior

### Session unlock model
The MVP has two distinct gates:

1. **Password gate**
   - Required to decrypt the vault on first unlock after boot.
   - Required again after a full re-lock.

2. **Required PIN gate**
   - After password decrypt, the backend re-wraps the whole vault into PIN-encrypted in-memory state.
   - PIN entry is required before vault contents become accessible during the session.
   - When the plugin is opened from the Decky sidebar while in the session-locked state, the first visible surface should be the PIN-entry screen.
   - The PIN-entry surface should be a numeric keypad suitable for handheld use.
   - Correct PIN entry should be accepted automatically on the final required digit, without a separate Enter or submit action.
   - Incorrect PIN entry should show immediate visible error feedback, including a red flash or equivalent failure cue, before allowing retry.
   - The PIN is a session-access gate layered on top of the password-based decrypt model, not a replacement for the password as the root vault secret.
   - PINs are numeric only, length 4 to 6 digits.
   - Derive the PIN key with **PBKDF2-SHA-256** at **200,000 iterations** and a separate random salt.

### Locked-state semantics
For the MVP, "locked" means the vault contents are inaccessible without PIN entry.

There are therefore two locked-like states that the implementation must distinguish:
- **fully locked / decrypt required**: vault is not available for use until the password decrypt flow succeeds
- **session locked / PIN required**: vault remains encrypted in memory under the PIN-derived key until the correct PIN is entered for a brief active operation window

This distinction is important to the UX, timeout behavior, and future biometric support.

### In-memory handling model
- The vault is managed by the Python backend.
- The whole vault may be decrypted only briefly for an active operation.
- After the operation, the backend must immediately re-encrypt the whole vault in memory with the PIN-derived key.
- Plaintext secret material should have the shortest practical lifetime.
- Plaintext memory must be zeroed after use.
- The implementation should avoid swap/pagefile exposure where practical.
- This is a hardened best-effort memory model, not an absolute guarantee against a sufficiently privileged local attacker.

## Clipboard model
- The default action when selecting a record is to copy the record password to the clipboard.
- The record view must also expose explicit actions to view, edit, and delete the record.
- Clipboard contents must be cleared automatically after a configurable timeout.
- Default clipboard timeout: **30 seconds**.
- The frontend may receive decrypted private values only for explicit view or copy actions.

The product should describe this as best-effort clipboard clearing rather than an absolute guarantee against OS-level observation.

## Record interaction model
### Session-locked entry behavior
- Opening the plugin from the Decky sidebar while session-locked should land directly on the numeric PIN pad.
- The user should not need to dismiss an intermediate screen before entering the PIN.
- PIN entry should optimize for thumb-friendly keypad use in the sidebar context.
- Successful entry should transition directly into the accessible record view.
- Failed entry should keep the user on the PIN pad and provide an immediate visible error cue.

### Default tap behavior
- Tapping/clicking a record performs the fast-path action: copy password to clipboard.

### Secondary actions
A separate affordance should allow the user to:
- inspect the full record
- view hidden fields intentionally
- edit the record
- delete the record

This keeps the common login flow fast while still allowing management operations.

### CLI expectations
- The CLI should use the same vault format, backend validation rules, and lock/unlock requirements as the UI path.
- The CLI is intended for local shell usage, including SSH sessions into the device.
- MVP commands are:
  - `<vault-command> add --key <key-id> --secret <secret> --name <name>`
  - `<vault-command> list`
  - `<vault-command> rm --key <key-id>`
  - `<vault-command> update --key <key-id> --secret <secret>`
- The CLI should also support `--secret-stdin` for large or shell-sensitive secret values.
- The CLI may support `--username` where relevant for record creation or update.
- Other CLI behavior is best-effort for MVP and should be documented as expectations rather than hard guarantees.

### Best-guess CLI authentication and failure behavior
- If the vault is fully locked, the CLI should prompt for the **master password** using non-echo terminal input.
- If the vault is not fully locked but is in the PIN-encrypted session state, the CLI should prompt for the **PIN** using non-echo terminal input.
- If `stdin` is already reserved for `--secret-stdin`, authentication prompts should read from `/dev/tty` when available rather than consuming piped secret input.
- If no interactive terminal is available and required authentication input was not provided through an approved mechanism, the command should fail cleanly with a clear message rather than falling back to insecure prompt behavior.
- Failed CLI authentication attempts should count toward the same password/PIN/recovery-key rate limits as UI attempts.
- On rate-limit hit, the CLI should exit non-zero and report that authentication is temporarily blocked.
- Best-guess exit behavior:
  - `0` for success
  - non-zero for validation errors, auth failures, lockouts, missing records, duplicate keys, or I/O failures
- Best-guess user-facing failure cases:
  - duplicate `--key` on `add` should fail and instruct the user to use `update`
  - unknown `--key` on `rm` or `update` should fail clearly
  - supplying both `--secret` and `--secret-stdin` should fail as invalid usage
  - omitted required arguments should produce help text and non-zero exit

## Future biometric extension
A future feature may allow a fingerprint sensor, when enabled on the device, to satisfy the access gate.

Current architectural implication:
- biometric unlock should be treated as a future unlock factor layered into the session access model
- the MVP must not depend on biometric hardware availability
- the architecture should avoid painting itself into a corner where password and PIN logic cannot later share a common access-gate interface

## Security posture for the MVP
The MVP security stance is:
- encrypted at rest is mandatory
- password-based decrypt is mandatory after boot and after full relock
- PIN is required and additive, not substitutive
- clipboard exposure is time-bounded and minimized, not eliminated
- local-only storage is mandatory
- secret values remain hidden by default outside intentional view/copy actions
- CLI-based secret entry is allowed only as another local device path, including over user-controlled SSH access

## Runtime state model
At minimum, implementation planning should distinguish these states:
- uninitialized vault
- locked, decrypt required
- unlocked, PIN gate active and currently locked
- unlocked and accessible
- relocking / timeout transition

This state model should drive both UI behavior and timeout handling.

## Timeout model
The MVP needs three configurable timers:

1. **Session access window**
   - after a successful PIN unlock, the vault is considered in use for a bounded period
   - default is **1 minute** since the most recent vault access
   - outside that window, the vault returns to PIN-encrypted in-memory state

2. **Full relock timeout**
   - after longer inactivity, the vault returns to the fully locked state
   - default is **6 hours**
   - once fully re-locked, master-password decrypt is required again

3. **Clipboard wipe timeout**
   - after copy, the clipboard is blanked after a delay
   - default is **30 seconds**

## Recovery and failure model
- Generate a recovery key as a **32-character base32 string**, grouped for readability, for example `ABCD-EFGH-IJKL-MNOP-QRST-UVWX-YZ12-3456`.
- The recovery key is shown to the user to store separately and is **not stored on the device**.
- Master-password changes require either the current password or the recovery key.
- PIN changes require the master password.
- Authentication failures for password, PIN, and recovery key count toward the same counters.
- Default rate limits are **5 failures per minute** and **20 failures per 10 minutes**, with configurability.
- Delete-on-failure is configurable, warns clearly, is off by default, and if enabled defaults to deleting the vault after **40 combined authentication failures**.

## Open architecture questions
These are intentionally still open and should be resolved before implementation is marked ready:
- how inactivity is detected for the 1-minute session access window and 6-hour full relock
- how notes are represented and bounded in the record model
- what guarantees are realistic for clipboard clearing under SteamOS and Decky runtime constraints
- whether any non-interactive CLI auth path is needed beyond the MVP best-guess interactive model

## Recommended delivery order
1. finalize architecture and threat model
2. define the state machine and trust boundaries clearly enough for implementation
3. build the Decky plugin skeleton
4. implement vault persistence and unlock model
5. implement record management UX
6. implement clipboard copy and timed wipe
7. implement the CLI path against the same backend
8. evaluate biometric extension separately as post-MVP work
