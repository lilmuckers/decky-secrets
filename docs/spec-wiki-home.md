# decky-secrets

`decky-secrets` is a Decky Loader plugin for Steam Deck / SteamOS that stores game-related credentials in a local encrypted vault and makes fast, time-bounded password retrieval practical during a live gaming session.

## MVP scope
- local encrypted vault stored on-device
- password-based decrypt on first unlock after boot and after full relock
- required secondary PIN gate after password unlock, with PIN-encrypted in-memory session state
- records containing name, username, password, and multiple notes
- fast password copy as the default record action
- automatic clipboard blanking after a configurable timeout, defaulting to 30 seconds

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
The project is still in the definition phase. The vault security baseline is now defined at the spec level, including AES-256-GCM at rest, PBKDF2-SHA-256 derivation settings, PIN-wrapped in-memory handling, recovery-key policy, and failure-throttling defaults. Backlog refinement and implementation-readiness work are still in progress. It is not yet ready for normal build execution.
