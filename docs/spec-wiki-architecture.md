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
- The vault must be cryptographically protected at rest.
- A password is required to decrypt the vault on first unlock after boot.
- A password is also required again after the vault has fully re-locked following a configurable inactivity timeout.
- The password-based unlock path is the root decrypt capability for the MVP.

### Session unlock model
The MVP has two distinct gates:

1. **Password gate**
   - Required to decrypt the vault on first unlock after boot.
   - Required again after a full re-lock.

2. **Optional PIN gate**
   - If enabled by the user, PIN entry is required before the already-decrypted vault contents become accessible.
   - The PIN is a local convenience/access-control gate layered on top of the password-based decrypt model, not a replacement for the password as the root vault secret.

### Locked-state semantics
For the MVP, "locked" means the vault contents are inaccessible without PIN entry.

There are therefore two locked-like states that the implementation must distinguish:
- **fully locked / decrypt required**: vault is not available for use until the password decrypt flow succeeds
- **session locked / PIN required**: vault may already be decrypted in memory, but record access remains blocked until the correct PIN is entered

This distinction is important to the UX, timeout behavior, and future biometric support.

## Clipboard model
- The default action when selecting a record is to copy the record password to the clipboard.
- The record view must also expose explicit actions to view, edit, and delete the record.
- Clipboard contents must be cleared automatically after a configurable timeout.
- Default clipboard timeout: **20 seconds**.

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

1. **Vault relock timeout**
   - after inactivity, the vault should leave the accessible state
   - once fully re-locked, password decrypt is required again

2. **Clipboard wipe timeout**
   - after copy, the clipboard is blanked after a delay
   - default is 20 seconds

The spec currently fixes the clipboard default but leaves the vault relock default to a follow-up product/security decision.

## Open architecture questions
These are intentionally still open and should be resolved before implementation is marked ready:
- which crypto and key-derivation libraries are suitable in the Decky / SteamOS environment
- exact file format for `~/.decky-secrets/vault`
- how inactivity is detected for vault relock timing
- how notes are represented and bounded in the record model
- whether PIN failure handling needs lockout/backoff in the MVP
- what guarantees are realistic for clipboard clearing under SteamOS and Decky runtime constraints

## Recommended delivery order
1. finalize architecture and threat model
2. define the state machine and trust boundaries clearly enough for implementation
3. build the Decky plugin skeleton
4. implement vault persistence and unlock model
5. implement record management UX
6. implement clipboard copy and timed wipe
7. evaluate biometric extension separately as post-MVP work
