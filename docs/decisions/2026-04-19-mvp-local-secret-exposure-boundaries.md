# Decision: MVP local secret exposure boundaries

- Status: accepted
- Date: 2026-04-19
- Owner: Security
- Related issue: #6

## Context
The MVP needed explicit implementation boundaries for the places where secrets can still be exposed on a local device even when the vault is encrypted at rest. The baseline crypto decision established the vault format and two-gate unlock model, but implementation work still needed concrete guardrails for clipboard handling, in-memory handling, lock semantics, local storage permissions, and crash or suspend edge cases.

## Decision
The MVP implementation must treat the following as hard security boundaries.

### 1. Clipboard boundary
- Copying a secret to the clipboard is an intentional exposure event.
- Clipboard exposure is allowed only after an explicit user action.
- The copied value must be auto-cleared after a configurable timeout, default **30 seconds**.
- Clipboard clearing must be described and implemented as **best effort**, not as a guaranteed wipe across all consumers, clipboard history tools, or already-pasted destinations.
- Copy confirmation UI must never echo the secret value back to the screen.
- The plugin must not keep a second redundant plaintext copy only to support the delayed clear; it should schedule the clear and release plaintext as soon as practical.

### 2. In-memory plaintext boundary while unlocked
- The backend may hold plaintext vault contents only during the shortest practical active operation window.
- "Unlocked" does not mean long-lived plaintext residency.
- The whole vault may be decrypted briefly inside the Python backend to satisfy an active operation, then must be re-encrypted in memory under the PIN-derived key immediately after that operation.
- Plaintext buffers must be zeroed or overwritten on the best-effort paths the implementation controls.
- Frontend state must not retain decrypted secret values except for the explicit reveal or copy workflow currently in progress.
- Routine list browsing, searching, and navigation must operate without exposing secret values to the frontend.

### 3. In-memory boundary while session-locked
- Session-locked state means the vault remains present only as PIN-encrypted in-memory material plus non-secret UI state.
- Session-locked state must block browsing secret contents, copying, reveal, edit, delete, and CLI access until the PIN succeeds.
- Session-locked state is not equivalent to full cryptographic erasure from RAM; the accepted MVP posture is that the vault is still recoverable by a sufficiently privileged attacker who can inspect process memory or runtime state.
- The implementation must never treat session-lock as protection against a hostile root user or equivalent local compromise.

### 4. Full-lock boundary
- Full lock means password decrypt is required again.
- On full lock, the process must discard the PIN-encrypted session blob, derived PIN key material, plaintext vault buffers, and any active-operation plaintext.
- After full lock, no CLI or UI path may regain access with PIN alone.

### 5. Local storage boundary
- Vault storage is fixed at `~/.decky-secrets/vault` for MVP.
- The parent directory should be created with permissions equivalent to `0700` where supported.
- The vault file should be created with permissions equivalent to `0600` where supported.
- The implementation should write atomically via a temporary file in the same directory followed by replace/rename, with restrictive permissions applied before sensitive bytes are written where practical.
- No plaintext vault export, plaintext cache file, debug dump, or clipboard backup file is allowed in MVP.
- Logs, metrics, and error messages must not include secret values, recovery keys, PINs, or master passwords.

### 6. Crash, restart, suspend, and timeout boundary
- Process restart or crash must be treated conservatively as loss of the active unlocked window.
- After backend restart, plugin restart, or system reboot, the vault must return to **fully locked** state requiring the master password.
- Suspend and resume must not silently extend an expired unlocked window. On resume, timers should be re-evaluated against real elapsed time.
- If a crash or restart occurs after a copy action, clipboard auto-clear may fail. That residual clipboard exposure is an accepted MVP risk and must be documented.
- Timeouts are security boundaries, not cosmetic UI timers. Expiry must revoke access before the next secret-bearing action.

### 7. Authentication throttling boundary
- Shared throttling across password, PIN, and recovery-key failures remains required.
- MVP rate limits of **5 failures per minute** and **20 failures per 10 minutes** are sufficient for the first release.
- Additional PIN-specific lockout rules are **not required** for MVP as long as the shared counters apply to both UI and CLI paths and lockout feedback is visible inline on the PIN pad.
- Permanent lockout is not required for MVP. Destructive delete-on-failure remains opt-in and off by default.

### 8. Future biometric boundary
- Any future biometric factor may satisfy only the **session access** gate unless a later security decision explicitly broadens its role.
- Biometric success must never bypass the master-password requirement after boot or after full relock in MVP-derived designs.
- Future biometric support must plug into the same session-gate interface and inherit the same timeout, throttling, and local-only trust boundaries.

## Concrete risks
1. Clipboard contents may be observed by the OS, other local software, clipboard history tooling, or the destination app before the timeout clears it.
2. Clipboard contents may survive a crash, suspend, or restart longer than intended.
3. A privileged local attacker may recover secrets from process memory, swap, crash dumps, or debugging interfaces while the vault is unlocked or session-locked.
4. Frontend state, logs, exceptions, or debug tooling could accidentally retain plaintext if implementation boundaries are sloppy.
5. Weak filesystem permissions or non-atomic writes could expose the encrypted blob or leak partial writes.
6. SSH access by the same local user expands the local attack surface for CLI use and clipboard-independent secret handling.
7. Fast PIN entry is weaker than the master password and therefore depends on throttling and the session-only trust boundary.

## Required mitigations
- Enforce restrictive file and directory permissions.
- Keep secret-bearing data in the backend unless a reveal or copy action explicitly requires frontend delivery.
- Re-wrap the vault under the PIN-derived key immediately after each active operation.
- Zero plaintext buffers on controlled paths.
- Avoid secret-bearing logs and error payloads.
- Apply shared auth throttling across UI and CLI paths.
- Re-evaluate timers on resume and treat restart as full lock.
- Document clipboard clearing honestly as best effort.

## Accepted MVP risks and non-goals
- The product does **not** protect against a hostile root user, kernel compromise, physical memory extraction, or forensic access to a fully compromised device.
- The product does **not** guarantee clipboard erasure from all OS buffers, clipboard managers, pasted destinations, or crash scenarios.
- The product does **not** guarantee perfect memory zeroization in a high-level runtime.
- The product does **not** attempt to disable screenshots, external cameras, keyloggers, or other endpoint-compromise classes of attack.
- The product does **not** provide a non-interactive remote automation path for vault unlock in MVP.
- The product does **not** treat biometrics as equivalent to the master password in MVP.

## Consequences
- Implementation issues must treat clipboard handling, frontend secret delivery, and timeout handling as security-sensitive behavior rather than UI polish.
- Session lock and full lock must remain distinct in code and in user-facing language.
- Builder and QA should test crash, resume, and timeout transitions explicitly.
- Architecture and issue docs should link to this decision when specifying unlock, copy, CLI, and local-storage behavior.
