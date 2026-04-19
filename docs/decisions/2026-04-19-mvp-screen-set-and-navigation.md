# Decision: MVP screen set and navigation model for Decky sidebar flows

- Status: accepted
- Date: 2026-04-19
- Owner: Spec

## Context
The project needed a more concrete user-facing screen model for the MVP Decky experience. The security and lock-state model were defined, but the main screens, navigation expectations, and sidebar-specific interaction constraints were still too implicit for implementation.

## Decision
The MVP Decky UI should be planned around these main screens:

1. first run / empty state
2. fully locked / master password unlock
3. session locked / numeric PIN pad
4. unlocked record list
5. record detail
6. add/edit record
7. copy confirmation / clipboard timeout cue

### Navigation model
- Opening the plugin enters one of three gate states: first run, fully locked, or session locked.
- After successful unlock, the user lands on the unlocked record list.
- Tapping a record in the unlocked list performs the default action: copy password.
- Record detail is reached through an explicit secondary affordance rather than the default row tap.
- Add starts from the record list.
- Edit starts from record detail.
- Session timeout or manual lock returns the user immediately to the appropriate lock screen.

### Screen-specific expectations
#### First run / empty state
- Explain the product briefly.
- Make vault creation the clear primary action.
- Keep setup reassurance short and avoid front-loading implementation details.

#### Fully locked / master password unlock
- Use a single password field with show/hide and an explicit unlock action.
- Clarify that the PIN is only for session re-entry after the vault has already been opened.

#### Session locked / PIN pad
- This is the first visible UI when the plugin is opened in the session-locked state.
- Use a thumb-friendly numeric keypad.
- The MVP Decky UI supports PIN entry lengths from 4 to 6 digits.
- Accept the PIN immediately on the final correct digit.
- Wrong PIN entry must produce immediate visible error feedback and clear the entered digits for retry.
- Temporary rate-limit lockout should be surfaced inline on the keypad rather than routing the user to a different unlock flow.

#### Unlocked record list
- This is the post-unlock home screen.
- Show search, add, manual lock, and a list of records.
- Preserve the fast-path behavior: tap a record to copy its password.
- Keep secret values hidden in the list.

#### Record detail
- Show non-secret metadata plus a masked password field.
- Require explicit action to reveal the secret.
- Use press-and-hold reveal behavior in MVP so the secret re-masks on release.
- Keep copy password as the primary action.
- Edit and delete stay secondary and explicit.

#### Add/edit record
- Keep the form compact.
- Require only the essential fields.
- Use inline validation and protect against accidental discard.

#### Copy confirmation / clipboard timeout cue
- Provide immediate, non-blocking confirmation that password copy succeeded.
- Show the clipboard timeout cue clearly enough that users know the copied value is temporary.

## Rationale
- The MVP succeeds or fails on fast in-session retrieval, so the session-locked PIN pad and unlocked record list must be especially clear.
- Explicit screen definitions reduce ambiguity for Builder and reduce the risk of generic form-like flows that are clumsy in the Decky sidebar.
- Keeping record detail behind a secondary affordance preserves the fast copy path while still supporting management actions.

## Consequences
- Issue #9 must implement the screen set and navigation expectations for the main Decky UI flow.
- Issue #5 must include copy confirmation and clipboard timeout feedback as part of the copy interaction, not as optional polish.
- Future design work can refine styling, but these screen roles and navigation expectations are now part of MVP product truth.

## Clarified MVP UX decisions
- The Decky UI supports PIN entry lengths from 4 to 6 digits in MVP.
- Repeated wrong PIN attempts stay on the keypad and surface temporary lockout feedback inline.
- Record detail is opened through a dedicated trailing details affordance in each row.
- Password reveal in record detail uses press-and-hold behavior.
- See `docs/decisions/2026-04-19-mvp-sidebar-ux-clarifications.md`.
