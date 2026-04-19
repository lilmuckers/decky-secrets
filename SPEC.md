# SPEC.md

## Purpose

`decky-secrets` is a Decky Loader extension for Steam Deck / SteamOS that lets a user keep game-related secrets in a local encrypted vault and quickly copy them to the pasteboard during a live session.

This file is the concise in-repo entrypoint. Deeper product and architecture context should live in the GitHub wiki.

## Project intent

- **Problem:** some games and launchers, especially third-party account systems, still require passwords or one-off secrets during startup and do not reliably remember them.
- **User:** Steam Deck users who want quick access to login secrets without keeping them in plain text notes or retyping them awkwardly in gaming mode.
- **Outcome:** users can unlock a local vault, select a stored secret, copy it briefly to the pasteboard, and continue playing.

## Scope summary

- **In scope:**
  - local encrypted secret storage on device at `~/.decky-secrets/vault`
  - password-based decrypt on first unlock after boot and after full relock
  - required secondary PIN gate for access during a running session after password unlock
  - Decky plugin UI for listing, adding, editing, deleting, viewing, and copying secrets
  - a local CLI tool for adding, listing, removing, and updating secrets in the vault, intended for technical users moving large or complex secrets over SSH
  - record fields for name, username, password, and multiple notes
  - clipboard / pasteboard copy action for a selected secret, with password copy as the default record action
  - automatic clipboard clearing after a short, configurable timeout, defaulting to 30 seconds
  - safe locked/unlocked state handling within a running session
  - configurable rate limiting for password, PIN, and recovery-key failures
- **Out of scope / non-goals:**
  - cloud sync
  - cross-device sharing
  - full password-manager feature parity
  - browser autofill
  - biometric unlock in the MVP, while keeping room for it later
  - broad secrets platform abstractions beyond Steam Deck / Decky needs

## User Flows

1. User opens the Decky plugin.
2. If the vault is fully locked, the user enters the master password to decrypt it.
3. The backend re-wraps the whole vault into PIN-encrypted in-memory state.
4. When the plugin is opened from the Decky sidebar during a session-locked state, the first visible surface is a numeric PIN pad.
5. User enters the required PIN on that pad and the vault unlocks as soon as the correct final digit is entered, without needing a separate submit action.
6. After unlock, the user lands on the record list screen.
7. User browses stored entries and selects one.
8. The default action copies the record password to the pasteboard for immediate use.
9. Clipboard is cleared automatically after a short timeout.

Secondary flows:
- first-time vault setup with recovery-key generation
- change master password with current password or recovery key
- change PIN with master password
- add/edit/delete a vault entry in the Decky UI
- add, list, remove, and update vault entries from the CLI over a shell or SSH session
- inspect a record in detail, including notes
- relock the vault manually

## Usability Requirements

- UI must be fast enough to use mid-session without feeling like a punishment.
- Copy flow should take as few taps as possible after unlock.
- When accessed from the Decky sidebar in a session-locked state, the plugin should open directly into a numeric PIN pad rather than an intermediate record view or extra unlock screen.
- The PIN flow should not require pressing Enter or tapping a submit button once the correct final digit has been entered.
- Incorrect PIN entry should produce immediate, obvious feedback, including a visible red error flash on the PIN pad.
- The unlocked state should land on a record list that supports fast scan, search, add, and manual lock without exposing secret values.
- The default record action should optimize for fast password copy.
- Record detail must be a secondary path, not the default tap target, and should be opened through a dedicated trailing details affordance.
- Password reveal in record detail should use press-and-hold behavior in MVP.
- Copy success should be confirmed immediately with a non-blocking clipboard timeout cue.
- Secret values should stay hidden by default.
- Revealing or copying a secret requires explicit user action.
- Timeout and locked-state cues should be obvious enough to prevent accidental exposure.
- The UI must make the difference between password decrypt and PIN re-entry understandable enough not to feel arbitrary.

## Design Direction

- Prefer a simple, native-feeling Decky UI over a clever one.
- Optimize for handheld use and low-friction interaction.
- Security-sensitive actions should be explicit, not decorative.
- The MVP Decky UI should be structured around a small, stable screen set: first run, fully locked unlock, session-locked PIN pad, unlocked record list, record detail, add/edit record, and copy confirmation feedback.
- The unlocked record list is the post-unlock home screen.
- Record detail should be reached through an explicit secondary affordance, because the default record tap remains reserved for fast password copy.

## Test Strategy

- **Required test types:** unit tests for vault logic, encryption boundary tests, clipboard timeout behavior tests, and integration tests for plugin state transitions where practical.
- **Tooling:** to be selected once the Decky plugin stack is confirmed.
- **Coverage expectations:** crypto-adjacent and state-transition behavior should be covered more heavily than cosmetic UI details.

## Acceptance Criteria

Top-level success conditions for the first useful version:

- User can create a local vault stored at `~/.decky-secrets/vault`.
- Vault remains encrypted at rest as a single AES-256-GCM encrypted blob.
- The master password key is derived with PBKDF2-SHA-256 at 600,000 iterations and a random salt.
- A fresh standard 96-bit AES-GCM nonce is used for each encryption operation.
- User must use a master password to decrypt the vault on first unlock after boot and after full relock.
- A PIN gate is required for session access after password unlock.
- The PIN is numeric only, 4 to 6 digits, and its key is derived with PBKDF2-SHA-256 at 200,000 iterations using a separate random salt.
- The MVP Decky UI uses a fixed 4-digit PIN flow.
- When the plugin is opened from the Decky sidebar while session-locked, the first UI shown is a numeric PIN pad.
- Correct PIN entry is accepted immediately when the final required digit is entered, without a separate submit step.
- Incorrect PIN entry produces immediate visible error feedback on the PIN pad before allowing retry.
- Temporary rate-limit lockout is surfaced inline on the PIN pad rather than routing to a different unlock flow.
- The whole vault is decrypted only briefly per active operation, then re-encrypted in memory with the PIN-derived key and plaintext memory is zeroed.
- User can create, edit, view, and delete records containing name, username, password, and multiple notes.
- User can add, list, remove, and update records from a local CLI tool without needing the Decky UI, to support shell and SSH-based entry of large or complex secrets.
- The CLI supports `add`, `list`, `rm`, and `update` commands, with secret input via either `--secret` or `--secret-stdin`.
- The CLI may accept `--username` where relevant for record creation or update.
- After successful unlock, the default home screen is the record list.
- Selecting a record copies its password to the pasteboard by default.
- Record detail is reached through an explicit secondary affordance rather than the default row tap.
- Copy success is confirmed immediately with a visible, non-blocking clipboard timeout cue.
- Copied password is automatically cleared from the pasteboard after a configurable timeout with a default of 30 seconds.
- Locked state prevents secret browsing and copying until the required password or PIN step has succeeded.
- Authentication failures for password, PIN, and recovery key are rate-limited, with defaults of 5 failures per minute and 20 failures per 10 minutes.
- Delete-on-failure is configurable, warns users clearly, and is off by default; if enabled, the default destructive threshold is 40 combined authentication failures.
- The frontend may receive decrypted private values only for explicit viewing or clipboard-copy workflows.
- No secret material is intentionally sent off-device.

## Current delivery intent

- **Current focus:** define architecture, storage model, unlock state model, threat boundaries, and the MVP backlog.
- **Important constraints:** Steam Deck / SteamOS environment, Decky Loader plugin model, local-only storage, encrypted-at-rest requirement, password-first decrypt model, required PIN-wrapped in-memory model, handheld UX, and a local CLI path for technical users.
- **Success indicators:** a stable plugin skeleton, clear vault model, explicit full-lock versus session-lock semantics, one end-to-end copy flow, a practical CLI ingest path, and a backlog decomposed into buildable issues.

## Authoritative wiki pages

- **Product definition:** Home
- **Solution design:** Architecture
- **Architecture:** Architecture
- **Decision records / assumptions:** Assumptions-and-decisions

## Notes

The first implementation should bias toward a narrow, trustworthy MVP.
A weak but small vault plugin is salvageable. A sprawling faux-password-manager is not.

See also:
- `docs/decisions/2026-04-19-mvp-screen-set-and-navigation.md`
- `docs/design/2026-04-19-mvp-sidebar-screen-mockups.md`
