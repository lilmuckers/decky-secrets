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

### D-004: PIN is required and wraps session memory
- A PIN gate is required after password unlock for session access.
- The vault remains encrypted in memory under a PIN-derived key except during the shortest practical active operation window.
- The PIN does not replace the password as the root vault unlock factor in MVP.
- Reason: this sidesteps the need to keep the vault plaintext in long-lived process memory while still supporting fast repeat access.

### D-005: Fingerprint support is future scope, not MVP scope
- Biometric unlock is a future extension only.
- The MVP architecture should leave room for it.
- Reason: hardware and platform support are variable, and the first release should not depend on them.

### D-006: Default record interaction copies the password
- Selecting a record copies its password to the clipboard by default.
- View, edit, and delete actions are secondary explicit actions.
- A local CLI tool may also add records directly into the vault for technical users working over shell or SSH.
- Reason: the dominant user job is quick password retrieval during a live session, while power users still need a practical path for entering large or complex secrets.

### D-007: Clipboard clearing is mandatory
- Copied clipboard contents are blanked after a timeout.
- Default timeout is 30 seconds.
- The timeout should remain configurable.
- Reason: clipboard persistence is one of the most obvious exposure points in this product.

### D-008: Locked does not always mean decrypted state is gone
- The product must distinguish between:
  - full lock, where password decrypt is required
  - session lock, where a PIN gate blocks access to vault contents and the vault remains PIN-encrypted in memory
- Reason: this matches the intended UX and creates a clean path for later biometric support.

### D-009: The vault crypto profile and library stack are fixed for MVP
- Encrypt the vault blob with AES-256-GCM.
- Use Python `hashlib.pbkdf2_hmac` for PBKDF2-SHA-256 derivation.
- Use the Python `cryptography` library for AES-GCM operations.
- Use Python `secrets` for random salt, nonce, and recovery-key generation.
- Derive the master-password key with PBKDF2-SHA-256 at 600,000 iterations and a random salt.
- Derive the PIN key with PBKDF2-SHA-256 at 200,000 iterations and a separate random salt.
- Use a fresh standard 96-bit AES-GCM nonce per encryption operation.
- Reason: this gives the MVP a concrete and reviewable cryptographic baseline with an implementation path that fits Python cleanly.

### D-010: Recovery key is user-held only
- Recovery uses a 32-character base32 string grouped for readability.
- The recovery key is not stored on the device.
- Recovery-key authentication failures count toward the same failure counters as password and PIN failures.
- Reason: recovery must remain available for password reset without weakening the device-local security posture.

### D-011: Failure throttling is required, destructive lockout is opt-in
- Combined authentication failures across password, PIN, and recovery key are rate-limited.
- Default limits are 5 failures per minute and 20 failures per 10 minutes.
- Delete-on-failure exists as an option, warns clearly, is off by default, and if enabled defaults to deleting the vault after 40 combined authentication failures.
- Reason: the MVP should slow guessing attacks by default without surprising users with destructive behavior.

### D-012: Full relock is configurable and defaults to 6 hours
- The session access window remains 1 minute by default.
- Full relock is a separate configurable timeout.
- The default full relock timeout is 6 hours.
- Reason: this preserves the fast session-gate model while still ensuring the vault eventually returns to password-only unlock.

### D-013: The MVP CLI surface is explicit and minimal
- The CLI supports `add`, `list`, `rm`, and `update` commands.
- Secret input should work via `--secret` or `--secret-stdin`.
- `--username` may be supported where relevant.
- Other CLI behavior is best-effort for MVP.
- Reason: this covers the intended SSH and power-user workflow without turning the first release into a full terminal password manager.

### D-014: The MVP best-guess vault schema is a versioned JSON blob with encrypted record payload
- The cleartext header should contain the format marker, version, master-password KDF metadata, cipher metadata, and ciphertext.
- The encrypted payload should contain vault timestamps, PIN data and KDF metadata, and the record array.
- Each record should use a stable unique `key` field as the CLI identifier.
- Reason: this is simple to serialize in Python, easy to migrate later, and matches the CLI and UI needs without premature complexity.

### D-015: The MVP CLI auth model is interactive and conservative by default
- Fully locked vault access prompts for the master password.
- Session-locked vault access prompts for the PIN.
- Prompts should use non-echo terminal input.
- When `--secret-stdin` is in use, prompts should read from `/dev/tty` when available.
- If secure interactive prompting is not possible, the CLI should fail rather than guess.
- Reason: this minimizes secret leakage and avoids unsafe prompt behavior in shell and SSH workflows.

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
- users can understand the distinction between password decrypt and required PIN re-entry without the UX becoming confusing

Why it matters:
- if the model feels confusing, the architecture may need simplification before build

### A-004: Storing multiple notes per record is still manageable in the MVP UI
Assumption:
- record detail UX can support multiple notes without turning the first release into a bloated editor experience

Why it matters:
- this affects the data model and the shape of the record editing UI

## Explicit non-decisions still open
These are not settled yet:
- maximum note size or record count expectations
- whether clipboard clearing should blank to empty string, overwrite, or use the best mechanism available in the environment
- whether any non-interactive CLI auth path is needed beyond the MVP interactive model

## Design implications for backlog refinement
These decisions imply:
- architecture work must cover both full-lock and session-lock states
- security investigation must treat clipboard exposure and in-memory accessible state as separate risks
- plugin skeleton work should avoid hard-coding assumptions that prevent a second access-gate factor later
- vault implementation work should assume `hashlib.pbkdf2_hmac`, `cryptography`, and `secrets`
- vault persistence work should treat the best-guess JSON blob schema as the default starting point
- copy flow work must describe clipboard wiping as configurable best-effort behavior
- CLI work must support both direct secret arguments and stdin-based secret entry
- CLI auth work should assume an interactive `/dev/tty` prompt model first

## Review trigger
This page should be revised whenever any of the following change materially:
- the root unlock model
- the meaning of locked state
- the default record interaction model
- the local storage path
- the MVP inclusion or exclusion of biometric support
