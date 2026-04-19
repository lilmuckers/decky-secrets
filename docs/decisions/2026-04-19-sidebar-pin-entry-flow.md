# Decision: Sidebar-first PIN entry flow for session unlock

- Status: accepted
- Date: 2026-04-19
- Owner: Spec

## Context
The project already required a numeric PIN gate for session access after the master password unlock. What was still too loose was the exact Decky sidebar unlock interaction. The product's main use case is quick retrieval during a live session, so an extra confirmation step after PIN entry would add friction directly to the critical path.

## Decision
For the MVP Decky sidebar flow:

1. When the plugin is opened while the vault is in the session-locked state, the first visible UI is a numeric PIN pad.
2. The user does not pass through an intermediate record list or separate unlock screen before the keypad.
3. The PIN pad is optimized for handheld sidebar use.
4. A correct PIN is accepted immediately when the final required digit is entered.
5. The user does not need to press Enter or tap a separate submit control.
6. A wrong PIN produces immediate visible failure feedback on the keypad, including a red flash or an equivalent error cue, before retry.

## Rationale
- The Decky sidebar context favors thumb-driven, low-friction interactions.
- The dominant job is quick access to an already-unlocked session vault, not form-style credential submission.
- Immediate success on the final digit removes an unnecessary extra action from the hottest path.
- Immediate failure feedback helps the user recover quickly without ambiguity.

## Consequences
- The record-management UI issue must include the session-locked keypad entry flow explicitly.
- PIN entry and PIN validation feedback are now part of MVP acceptance, not implementation detail.
- Builders should avoid a generic text-input-plus-submit design for the sidebar unlock flow unless a platform constraint forces it and that change is re-approved.

## Rejected alternative
- **Generic text entry with explicit submit:** rejected because it adds avoidable friction in the sidebar context and does not match the intended handheld quick-access workflow.
