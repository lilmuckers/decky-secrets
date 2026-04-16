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
  - optional secondary PIN gate for access after password unlock
  - Decky plugin UI for listing, adding, editing, deleting, viewing, and copying secrets
  - record fields for name, username, password, and multiple notes
  - clipboard / pasteboard copy action for a selected secret, with password copy as the default record action
  - automatic clipboard clearing after a short, configurable timeout, defaulting to 20 seconds
  - safe locked/unlocked state handling within a running session
- **Out of scope / non-goals:**
  - cloud sync
  - cross-device sharing
  - full password-manager feature parity
  - browser autofill
  - biometric unlock in the MVP, while keeping room for it later
  - broad secrets platform abstractions beyond Steam Deck / Decky needs

## User Flows

1. User opens the Decky plugin.
2. If the vault is fully locked, the user enters the password to decrypt it.
3. If a secondary PIN gate is enabled, the user enters the PIN before vault contents become accessible.
4. User browses stored entries and selects one.
5. The default action copies the record password to the pasteboard for immediate use.
6. Clipboard is cleared automatically after a short timeout.

Secondary flows:
- first-time vault setup
- enable or disable the secondary PIN gate
- add/edit/delete a vault entry
- inspect a record in detail, including notes
- relock the vault manually

## Usability Requirements

- UI must be fast enough to use mid-session without feeling like a punishment.
- Copy flow should take as few taps as possible after unlock.
- The default record action should optimize for fast password copy.
- Secret values should stay hidden by default.
- Timeout and locked-state cues should be obvious enough to prevent accidental exposure.
- The UI must make the difference between password decrypt and optional PIN re-entry understandable enough not to feel arbitrary.

## Design Direction

- Prefer a simple, native-feeling Decky UI over a clever one.
- Optimize for handheld use and low-friction interaction.
- Security-sensitive actions should be explicit, not decorative.

## Test Strategy

- **Required test types:** unit tests for vault logic, encryption boundary tests, clipboard timeout behavior tests, and integration tests for plugin state transitions where practical.
- **Tooling:** to be selected once the Decky plugin stack is confirmed.
- **Coverage expectations:** crypto-adjacent and state-transition behavior should be covered more heavily than cosmetic UI details.

## Acceptance Criteria

Top-level success conditions for the first useful version:

- User can create a local vault stored at `~/.decky-secrets/vault`.
- Vault remains encrypted at rest.
- User must use a password to decrypt the vault on first unlock after boot and after full relock.
- User may optionally enable a secondary PIN gate for access after password unlock.
- User can create, edit, view, and delete records containing name, username, password, and multiple notes.
- Selecting a record copies its password to the pasteboard by default.
- Copied password is automatically cleared from the pasteboard after a configurable timeout with a default of 20 seconds.
- Locked state prevents secret browsing and copying until the required password or PIN step has succeeded.
- No secret material is intentionally sent off-device.

## Current delivery intent

- **Current focus:** define architecture, storage model, unlock state model, threat boundaries, and the MVP backlog.
- **Important constraints:** Steam Deck / SteamOS environment, Decky Loader plugin model, local-only storage, encrypted-at-rest requirement, password-first decrypt model, optional PIN gate, handheld UX.
- **Success indicators:** a stable plugin skeleton, clear vault model, explicit full-lock versus session-lock semantics, one end-to-end copy flow, and a backlog decomposed into buildable issues.

## Authoritative wiki pages

- **Product definition:** Home
- **Solution design:** Architecture
- **Architecture:** Architecture
- **Decision records / assumptions:** Assumptions-and-decisions

## Notes

The first implementation should bias toward a narrow, trustworthy MVP.
A weak but small vault plugin is salvageable. A sprawling faux-password-manager is not.