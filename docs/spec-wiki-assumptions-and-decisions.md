# Assumptions and decisions

## Status
This page records the current project-level assumptions and decisions for the `decky-secrets` MVP.

Some items below are settled decisions for the MVP. Others are explicit open assumptions that still need confirmation before implementation is considered ready.

## Settled MVP decisions

### D-001: The vault is local-only
- Vault data lives on the device only.
- No cloud sync, replication, or off-device transport is in MVP scope.
- Reason: this sharply reduces scope and trust-surface area for the first release.

### D-002: Vault storage path is fixed for the MVP
- The vault is stored at `~/.decky-secrets/vault`.
- Reason: a stable location simplifies support, documentation, and migration planning.

### D-003: Password unlock is the root decrypt mechanism
- A password is required to decrypt on first boot.
- A password is required again after full relock caused by timeout.
- Reason: the project needs a strong primary secret and should not treat a short PIN as the sole basis for decrypting the vault.

### D-004: PIN is optional and additive
- Users may optionally enable a PIN gate after password unlock.
- The PIN controls access to an already decrypted or decrypt-ready session state.
- The PIN does not replace the password as the root vault unlock factor in MVP.
- Reason: this preserves fast repeat access while keeping the password as the stronger primary secret.

### D-005: Fingerprint support is future scope, not MVP scope
- Biometric unlock is a future extension only.
- The MVP architecture should leave room for it.
- Reason: hardware and platform support are variable, and the first release should not depend on them.

### D-006: Default record interaction copies the password
- Selecting a record copies its password to the clipboard by default.
- View, edit, and delete actions are secondary explicit actions.
- Reason: the dominant user job is quick password retrieval during a live session.

### D-007: Clipboard clearing is mandatory
- Copied clipboard contents are blanked after a timeout.
- Default timeout is 20 seconds.
- The timeout should remain configurable.
- Reason: clipboard persistence is one of the most obvious exposure points in this product.

### D-008: Locked does not always mean decrypted state is gone
- The product must distinguish between:
  - full lock, where password decrypt is required
  - session lock, where a PIN gate blocks access to vault contents
- Reason: this matches the intended UX and creates a clean path for later biometric support.

## Current assumptions to validate

### A-001: SteamOS / Decky can support the required crypto stack cleanly
Assumption:
- the target environment can support a vetted cryptographic implementation and necessary key-derivation functions without awkward packaging or runtime compromises

Why it matters:
- if false, the chosen architecture may not be practical for the plugin runtime

### A-002: Clipboard blanking is implementable as a reliable best-effort control
Assumption:
- the plugin can clear or overwrite clipboard contents after a timeout in a way that is meaningful to users and not excessively brittle

Why it matters:
- clipboard wipe behavior is part of the core value and risk posture

### A-003: A two-gate session model is understandable in the UI
Assumption:
- users can understand the distinction between password decrypt and optional PIN re-entry without the UX becoming confusing

Why it matters:
- if the model feels confusing, the architecture may need simplification before build

### A-004: Storing multiple notes per record is still manageable in the MVP UI
Assumption:
- record detail UX can support multiple notes without turning the first release into a bloated editor experience

Why it matters:
- this affects the data model and the shape of the record editing UI

## Explicit non-decisions still open
These are not settled yet:
- exact cryptographic algorithm and library selection
- exact vault file schema and migration strategy
- vault relock default duration
- whether PIN retry throttling or lockout is required in MVP
- maximum note size or record count expectations
- whether clipboard clearing should blank to empty string, overwrite, or use the best mechanism available in the environment

## Design implications for backlog refinement
These decisions imply:
- architecture work must cover both full-lock and session-lock states
- security investigation must treat clipboard exposure and in-memory accessible state as separate risks
- plugin skeleton work should avoid hard-coding assumptions that prevent a second access-gate factor later
- vault implementation work is blocked on the crypto/runtime decision
- copy flow work must describe clipboard wiping as configurable best-effort behavior

## Review trigger
This page should be revised whenever any of the following change materially:
- the root unlock model
- the meaning of locked state
- the default record interaction model
- the local storage path
- the MVP inclusion or exclusion of biometric support
