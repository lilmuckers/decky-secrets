# decky-secrets

A Decky Loader extension for Steam Deck / SteamOS that stores user secrets locally in an encrypted vault and makes them easy to copy to the pasteboard during a running gaming session.

## Why this exists

Some games and launchers still ask for passwords at awkward times and do a terrible job remembering them. `decky-secrets` aims to make that less annoying without turning the Steam Deck into a secret-spilling disaster.

## Intended MVP

- store named secrets in a local encrypted vault
- unlock the vault with either a PIN or a password
- browse and manage secrets from a Decky plugin UI
- copy a selected secret to the pasteboard for use in the current session
- auto-clear copied secrets from the pasteboard after a short timeout
- keep all secret material local to the device

## Non-goals for the first cut

- cloud sync
- multi-device vault replication
- browser autofill
- password generation and full password-manager scope creep
- long-lived clipboard retention

## Project status

Framework bootstrap is in progress. See `SPEC.md` and `docs/delivery/` for delivery state and project definition.