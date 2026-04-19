# Decision: MVP sidebar UX clarifications

- Status: accepted
- Date: 2026-04-19
- Owner: Spec

## Context
The initial MVP screen-set work surfaced a handful of open UX questions that were small enough to resolve now, but important enough that leaving them open would create avoidable ambiguity for implementation.

## Decision
For the MVP Decky sidebar flow:

1. **PIN length in the UI is fixed to 4 digits.**
   - The broader security model may still allow 4 to 6 digits as an internal policy range, but the MVP Decky UI should implement a fixed 4-digit PIN flow.
   - Reason: the design work and keypad interaction are cleaner and faster with a single expected length.

2. **Wrong PIN attempts stay on the PIN pad and are rate-limited, not escalated into a new recovery flow by default.**
   - If rate limiting blocks further attempts temporarily, the PIN pad should remain visible and show a cooldown/try-again-later message.
   - The MVP should not introduce a separate in-flow master-password fallback path from the session-locked keypad unless later platform constraints force it.
   - Reason: this keeps the common path simple and consistent with the existing combined failure-throttling policy.

3. **Record detail is opened through a dedicated trailing details affordance in each record row.**
   - The default row tap remains password copy.
   - The detail affordance should be visible and explicit, for example a chevron or details button on the right side of the row.
   - The MVP should not rely on long-press as the primary detail-discovery mechanism.
   - Reason: long-press is less discoverable and less reliable across touch/controller use in the sidebar context.

4. **Password reveal in record detail uses press-and-hold behavior.**
   - The password remains masked by default.
   - Releasing the hold returns the field to the masked state.
   - Reason: this reduces accidental prolonged exposure compared with a sticky toggle while still supporting intentional inspection.

## Consequences
- The PIN pad mockup and issue wording should describe a fixed 4-digit entry expectation.
- The screen mockups should describe temporary lockout feedback on the keypad rather than a fallback route to a different unlock screen.
- The record list mockups and issue wording should call for a dedicated secondary details affordance in each row.
- The record detail mockup should describe reveal as press-and-hold, not an ambiguous hold/toggle choice.

## Rejected alternatives
- **Configurable PIN length in the MVP UI:** rejected for now because it adds extra UI and testing complexity to the hottest path.
- **Long-press to open record detail:** rejected because it is less discoverable in the sidebar context.
- **Sticky password reveal toggle as the default reveal model:** rejected because it increases shoulder-surfing risk.
