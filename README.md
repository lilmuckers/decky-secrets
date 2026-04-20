# decky-secrets

A Decky Loader plugin for Steam Deck / SteamOS that will eventually store user secrets locally in an encrypted vault and make them easy to copy during a running gaming session.

## Current status

Issues #3, #4, #5, #7, and #8 establish the initial Decky plugin scaffold, the Python encrypted-vault persistence layer, the scoped clipboard copy flow, the backend lock/auth state model, and the local CLI command surface.

What exists now:
- Decky plugin metadata in `plugin.json`
- a TypeScript frontend panel in `src/index.tsx`
- a Python backend entrypoint in `main.py`
- a testable Python vault module in `decky_secrets/vault.py`
- a testable Python clipboard service in `decky_secrets/clipboard.py`
- a local Python CLI in `decky_secrets/cli.py` with `add`, `list`, `rm`, and `update`
- Rollup and TypeScript build config for the current Decky template toolchain
- an unlocked record list slice that performs password copy as the default action
- immediate copy confirmation with a visible clipboard timeout cue and best-effort wording
- encrypted-at-rest vault creation and load support at `~/.decky-secrets/vault`
- backend lock-state handling for `decrypt_required`, `session_locked`, and `accessible`
- shared auth throttling and full-relock/session-timeout behavior for backend callers
- unit tests for blob shape, permissions, decrypt, auth transitions, restart/full-lock behavior, throttling, clipboard copy gating, and CLI command behavior

What is intentionally **not** implemented yet:
- broader Decky record-management UI, reveal flows, or edit/delete implementations
- biometric unlock
- additional CLI commands beyond `add`, `list`, `rm`, and `update`

## Repository layout

```text
.
├── backend/              # reserved for future backend build artifacts/source
├── decky_secrets/        # Python vault persistence, lock-state, auth, clipboard, and CLI modules
├── docs/                 # spec, architecture, decisions, delivery state
├── main.py               # live Decky Python backend entrypoint
├── package.json          # frontend toolchain config
├── plugin.json           # Decky plugin metadata
├── requirements.txt      # Python backend dependency pinning
├── rollup.config.js      # Decky Rollup build config
├── src/index.tsx         # placeholder Decky sidebar UI
├── tests/test_auth.py    # Python unit tests for lock/auth behavior
├── tests/test_vault.py   # Python unit tests for persistence layer
└── tsconfig.json         # TypeScript compiler settings
```

The current backend keeps room for the documented Python-owned vault model and the distinct full-lock versus session-lock states defined in `SPEC.md` and `docs/spec-wiki-architecture.md`.

## Local development

### Install prerequisites

For the current toolchain, install:
- Node.js 16.14 or newer
- `pnpm` 9.x
- Python 3.11 or newer
- the Python `cryptography` package from `requirements.txt`
- Decky Loader on the target Steam Deck / SteamOS device

Example:

```bash
npm install -g pnpm@9
python3 -m pip install -r requirements.txt
```

From a fresh checkout, install frontend dependencies with:

```bash
pnpm install
```

## Build

Build the plugin frontend with:

```bash
pnpm build
```

This should produce the Decky frontend bundle at `dist/index.js`.

For active frontend work, use:

```bash
pnpm watch
```

## Run

### CLI usage

Use the local CLI with:

```bash
python3 -m decky_secrets list
python3 -m decky_secrets add --key battle-net --name "Battle.net" --secret "example"
printf 'stdin-secret' | python3 -m decky_secrets update --key battle-net --secret-stdin
python3 -m decky_secrets rm --key battle-net
```

The CLI uses the same auth boundary as the backend. When fully locked it prompts for the master password and then the session PIN. When stdin is reserved for `--secret-stdin`, it prefers `/dev/tty` for auth prompts and fails cleanly if a secure prompt path is unavailable.


On a Steam Deck with Decky Loader installed, copy this repository into the Decky plugins directory under the plugin folder name `decky-secrets`.

Typical layout on device:

```text
~/homebrew/plugins/decky-secrets/
  dist/
  main.py
  plugin.json
  package.json
```

If you are developing from another machine, `rsync` or `scp` the repository contents over after building.

After copying the plugin files onto the device:

1. restart Decky Loader
2. open the Decky sidebar
3. open **Decky Secrets**

## Verify

For the current scaffold plus persistence/auth slices, verify the following:

1. `pnpm install` succeeds on a fresh checkout
2. `pnpm build` produces `dist/index.js`
3. `python3 -m unittest tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli` passes
4. `pnpm test:frontend` passes
5. `python3 -m decky_secrets list` shows non-secret record fields only after successful auth
6. Decky Loader shows the `Decky Secrets` plugin in the sidebar
7. opening the plugin renders the panel successfully
8. when backend state is `accessible`, using the record copy action shows copy confirmation plus the timeout cue without echoing the secret value
9. the UI describes clipboard clearing as best effort rather than a guaranteed wipe
10. fresh copy actions are blocked when backend state is `decrypt_required` or `session_locked`
11. CLI invalid usage, duplicate keys, missing keys, and auth failures exit non-zero with clear non-secret messages
12. a backend-created vault file remains encrypted at rest and is not readable as plaintext JSON secret data
13. backend timeout and restart tests prove the session window expires back to `session_locked` and the full relock path returns to `decrypt_required`

## Product direction

The target MVP remains:
- local encrypted secret storage at `~/.decky-secrets/vault`
- password-first decrypt after boot and after full relock
- required PIN-gated session access
- Decky UI for browsing and managing records
- local CLI support for technical users

The clipboard clear timeout defaults to 30 seconds and can be adjusted for local testing with the environment variable `DECKY_SECRETS_CLIPBOARD_CLEAR_SECONDS`.

Clipboard clearing remains best effort only. It does not claim to wipe clipboard history tools, pasted destinations, or crash/restart remnants.

For the authoritative product and architecture definition, see:
- `SPEC.md`
- `docs/spec-wiki-home.md`
- `docs/spec-wiki-architecture.md`
- `docs/spec-wiki-assumptions-and-decisions.md`
- `docs/decisions/2026-04-18-vault-security-baseline.md`
