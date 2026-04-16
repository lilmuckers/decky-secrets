# decky-secrets

`decky-secrets` is a Decky Loader plugin for Steam Deck / SteamOS that stores game-related credentials in a local encrypted vault and makes fast, time-bounded password retrieval practical during a live gaming session.

## MVP scope
- local encrypted vault stored on-device
- password-based decrypt on first unlock after boot and after full relock
- optional secondary PIN gate after password unlock
- records containing name, username, password, and multiple notes
- fast password copy as the default record action
- automatic clipboard blanking after a configurable timeout, defaulting to 20 seconds

## Non-goals
- cloud sync
- multi-device replication
- browser autofill
- full password-manager scope
- biometric unlock in the MVP

## Key pages
- [[Architecture]]
- [[Assumptions-and-decisions]]

## Current project status
The project is still in the definition phase. Architecture, threat model, and backlog refinement are in progress. It is not yet ready for normal build execution.
