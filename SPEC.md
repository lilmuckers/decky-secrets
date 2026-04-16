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
  - local encrypted secret storage on device
  - unlock flow using either a PIN or a password
  - Decky plugin UI for listing, adding, editing, deleting, and copying secrets
  - clipboard / pasteboard copy action for a selected secret
  - automatic clipboard clearing after a short, configurable timeout
  - safe locked/unlocked state handling within a running session
- **Out of scope / non-goals:**
  - cloud sync
  - cross-device sharing
  - full password-manager feature parity
  - browser autofill
  - broad secrets platform abstractions beyond Steam Deck / Decky needs

## User Flows

1. User opens the Decky plugin.
2. If the vault is locked, user unlocks it with a PIN or password.
3. User browses stored entries and selects one.
4. User taps copy.
5. Secret is placed onto the pasteboard for immediate use.
6. Clipboard is cleared automatically after a short timeout.

Secondary flows:
- first-time vault setup
- change unlock method or rotate master credential
- add/edit/delete a vault entry
- relock the vault manually

## Usability Requirements

- UI must be fast enough to use mid-session without feeling like a punishment.
- Copy flow should take as few taps as possible after unlock.
- Secret values should stay hidden by default.
- Timeout and locked-state cues should be obvious enough to prevent accidental exposure.

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

- User can create a local vault and protect it with either a PIN or a password.
- Vault remains encrypted at rest.
- User can create, edit, and delete named secret entries.
- User can unlock the vault and copy a selected secret to the pasteboard.
- Copied secret is automatically cleared from the pasteboard after a timeout.
- Locked state prevents secret browsing and copying until re-authenticated.
- No secret material is intentionally sent off-device.

## Current delivery intent

- **Current focus:** define architecture, storage model, threat boundaries, and the MVP backlog.
- **Important constraints:** Steam Deck / SteamOS environment, Decky Loader plugin model, local-only storage, encrypted-at-rest requirement, handheld UX.
- **Success indicators:** a stable plugin skeleton, clear vault model, one end-to-end copy flow, and a backlog decomposed into buildable issues.

## Authoritative wiki pages

- **Product definition:** Home
- **Solution design:** Architecture
- **Architecture:** Architecture
- **Decision records / assumptions:** Assumptions and decisions

## Notes

The first implementation should bias toward a narrow, trustworthy MVP.
A weak but small vault plugin is salvageable. A sprawling faux-password-manager is not.