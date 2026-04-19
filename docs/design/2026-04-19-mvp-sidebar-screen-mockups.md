# MVP sidebar screen mockups

- Status: draft design reference adopted by Spec on 2026-04-19
- Purpose: low-fidelity screen reference for the Decky sidebar MVP flows

This document gives Builder a concrete screen model for the main Decky UI without locking the project into pixel-perfect styling.

## Recommended MVP screen set
1. first run / empty state
2. fully locked / master password unlock
3. session locked / numeric PIN pad
4. unlocked record list
5. record detail
6. add/edit record
7. copy confirmation / clipboard timeout cue

## Navigation model
- Opening the plugin lands in one of three gate states: first run, fully locked, or session locked.
- After successful unlock, the user lands on the unlocked record list.
- Default record tap copies the password immediately.
- Record detail is reached through an explicit secondary affordance.
- Add begins from the record list.
- Edit begins from record detail.
- Timeout or manual lock returns the user to the appropriate lock screen.

## 1) First run / empty state
**Purpose**
Explain the product briefly and make vault creation the obvious first action.

```text
[Header]
Decky Secrets

[Body]
No vault yet

Store passwords for quick access in-game.
Secrets stay hidden by default.
You can unlock with:
- Master password
- Quick session PIN

[Primary CTA]
Create vault

[Secondary]
Learn how it works
```

## 2) Fully locked / master password unlock
**Purpose**
Unlock the vault from the cold-locked state with the master password.

```text
[Header]
Unlock vault

[Body]
Master password required

[Password Field]
••••••••••••
[Show/Hide]

[Primary CTA]
Unlock

[Secondary]
Use keyboard
Forgot? (optional/help text only)

[Footer hint]
Session PIN works only after the vault has been opened once this session.
```

## 3) Session locked / numeric PIN pad
**Purpose**
Provide the fast re-entry surface for the common in-session case.

```text
[Header]
Enter PIN

[PIN Dots]
● ● ○ ○

[Numeric Pad]
[1] [2] [3]
[4] [5] [6]
[7] [8] [9]
[⌫] [0] [Lock]

[Hint]
Enter 4-digit PIN

[Feedback area]
Wrong PIN
or
Too many attempts, try again in 30s
```

Interaction notes:
- first visible UI when the plugin opens in the session-locked state
- fixed 4-digit PIN in the MVP UI
- accepts the correct PIN immediately on the final required digit
- wrong PIN produces immediate visible feedback and clears entered digits for retry
- temporary rate-limit lockout is shown inline on the keypad rather than routing to a different unlock flow
- no explicit submit button

## 4) Unlocked record list
**Purpose**
Serve as the post-unlock home screen and fast password-copy surface.

```text
[Header]
Secrets                         [+]
[Search]
Search records...

[List]
> Email
  user@example.com              [Copy on tap] [Details >]

> Battle.net
  masked / optional subtitle    [Details >]

> Wi-Fi
  Home network                  [Details >]

[Footer / utility]
Clipboard clears in 30s
[Lock]
```

Interaction notes:
- record tap copies password by default
- each row includes a dedicated trailing details affordance
- list supports search, add, and manual lock
- secrets stay hidden in the list

## 5) Record detail
**Purpose**
Allow explicit inspection and management without exposing the secret by default.

```text
[Header]
Battle.net                     [Edit]

[Fields]
Label
Battle.net

Username
player123

Password
••••••••••••••
[Press and hold to reveal]   [Copy]

Notes
2FA backup email in personal inbox

[Actions]
Copy password
Copy username
Lock vault
Delete (secondary / danger)
```

Interaction notes:
- secret remains masked by default
- reveal uses press-and-hold behavior and returns to masked on release
- copy password is still the primary action inside detail
- delete requires confirmation

## 6) Add/edit record
**Purpose**
Create or update records with a compact form suitable for sidebar use.

```text
[Header]
Add record
or
Edit record

[Form]
Label *
[ Battle.net ]

Username
[ player123 ]

Password *
[ •••••••••••• ] [Show/Hide]

Notes
[ Optional note text... ]

[Actions]
Save
Cancel
```

Interaction notes:
- keep required fields minimal
- use inline validation
- protect against accidental discard when fields have changed

## 7) Copy confirmation / clipboard timeout cue
**Purpose**
Confirm success without blocking navigation or revealing secrets.

```text
[Toast / inline banner]
Password copied

[Secondary line]
Clipboard clears in 30s

[Optional action]
Copy username
```

Interaction notes:
- should appear immediately after copy
- should not block movement through the UI
- should not expose the copied secret value itself

## Main usability risks
- accidental taps on narrow record rows
- users expecting row tap to open detail instead of copy
- keyboard friction for master password and form entry
- truncation pressure in the narrow sidebar layout
- poor PIN retry clarity if failure feedback is weak
- overexposed feedback that reveals too much to shoulder surfers

## Resolved MVP clarifications
- the Decky UI uses a fixed 4-digit PIN flow for MVP
- repeated wrong PIN attempts stay on the keypad and surface temporary lockout feedback inline
- record detail is opened through a dedicated trailing details affordance on each row
- password reveal in detail uses press-and-hold behavior rather than a sticky toggle
