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

### Encryption model
- The vault must be cryptographically protected at rest as a single encrypted blob.
- Use **AES-256-GCM** for vault encryption.
- Derive the master-password key with **PBKDF2-SHA-256** at **600,000 iterations** and a separate random salt.
- Use a fresh standard **96-bit AES-GCM nonce** for each encryption operation.
- A password is required to decrypt the vault on first unlock after boot.
- A password is also required again after the vault has fully re-locked following a configurable inactivity timeout.
- The password-based unlock path is the root decrypt capability for the MVP.

### Session unlock model
The MVP has two distinct gates:

1. **Password gate**
   - Required to decrypt the vault on first unlock after boot.
   - Required again after a full re-lock.

2. **Required PIN gate**
   - After password decrypt, the backend re-wraps the whole vault into PIN-encrypted in-memory state.
   - PIN entry is required before vault contents become accessible during the session.
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
### Default tap behavior
- Tapping/clicking a record performs the fast-path action: copy password to clipboard.

### Secondary actions
A separate affordance should allow the user to:
- inspect the full record
- view hidden fields intentionally
- edit the record
- delete the record

This keeps the common login flow fast while still allowing management operations.

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
- PIN is optional and additive, not substitutive
- clipboard exposure is time-bounded and minimized, not eliminated
- local-only storage is mandatory
- secret values remain hidden by default outside intentional view/copy actions

## Runtime state model
At minimum, implementation planning should distinguish these states:
- uninitialized vault
- locked, decrypt required
- unlocked, no secondary gate configured
- unlocked, PIN gate active and currently locked
- unlocked and accessible
- relocking / timeout transition

This state model should drive both UI behavior and timeout handling.

## Timeout model
The MVP needs two configurable timers:

1. **Session access window**
   - after a successful PIN unlock, the vault is considered in use for a bounded period
   - default is **1 minute** since the most recent vault access
   - outside that window, the vault returns to PIN-encrypted in-memory state

2. **Clipboard wipe timeout**
   - after copy, the clipboard is blanked after a delay
   - default is **30 seconds**

A separate full-relock timeout may still exist, but the session-access window is the main default locked-state timer defined for the MVP.

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
- which crypto and key-derivation libraries are suitable in the Decky / SteamOS environment
- exact file format versioning and metadata layout for `~/.decky-secrets/vault`
- how inactivity is detected for full relock timing beyond the 1-minute session access window
- how notes are represented and bounded in the record model
- what guarantees are realistic for clipboard clearing under SteamOS and Decky runtime constraints

## Recommended delivery order
1. finalize architecture and threat model
2. define the state machine and trust boundaries clearly enough for implementation
3. build the Decky plugin skeleton
4. implement vault persistence and unlock model
5. implement record management UX
6. implement clipboard copy and timed wipe
7. evaluate biometric extension separately as post-MVP work
