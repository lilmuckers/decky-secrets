# decky-secrets

A Decky Loader plugin for Steam Deck / SteamOS that will eventually store user secrets locally in an encrypted vault and make them easy to copy during a running gaming session.

## Current status

Issues #3, #4, #5, #7, #8, #9, and #17 establish the initial Decky plugin scaffold, the Python encrypted-vault persistence layer, the scoped clipboard copy flow, the backend lock/auth state model, the local CLI command surface, the first Decky record-management UI flows, and the packaged Decky backend import-layout fix for the plugin sandbox.

What exists now:
- Decky plugin metadata in `plugin.json`
- a TypeScript frontend panel in `src/index.tsx`
- a Python backend entrypoint in `main.py`
- a backend bootstrap that places the plugin root on `sys.path` before importing bundled Python modules in the Decky sandbox
- a testable Python vault module in `decky_secrets/vault.py`
- a testable Python clipboard service in `decky_secrets/clipboard.py`
- a local Python CLI in `decky_secrets/cli.py` with `add`, `list`, `rm`, and `update`
- Rollup and TypeScript build config for the current Decky template toolchain
- Decky first-run, master-password unlock, session-locked PIN pad, unlocked list, detail, and add/edit/delete flows
- an unlocked record list home screen that performs password copy as the default row action
- dedicated record-detail navigation, masked-by-default detail rendering, and press-and-hold password reveal
- immediate copy confirmation with a visible clipboard timeout cue and best-effort wording
- encrypted-at-rest vault creation and load support at `~/.decky-secrets/vault`
- backend lock-state handling for `decrypt_required`, `session_locked`, and `accessible`
- shared auth throttling and full-relock/session-timeout behavior for backend callers
- unit tests for blob shape, permissions, decrypt, auth transitions, restart/full-lock behavior, throttling, clipboard copy gating, and CLI command behavior

What is intentionally **not** implemented yet:
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
├── src/index.tsx         # Decky sidebar UI flows
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

The CLI uses the same auth boundary as the backend, but the shipped `python3 -m decky_secrets ...` surface is a one-shot process model. In practice each CLI invocation starts from a fresh auth manager, so each command conservatively prompts for the master password and then the session PIN rather than reusing a session-locked state across invocations. When stdin is reserved for `--secret-stdin`, it prefers `/dev/tty` for auth prompts and fails cleanly if a secure prompt path is unavailable.


On a Steam Deck with Decky Loader installed, copy this repository into the Decky plugins directory under the plugin folder name `decky-secrets`.

Typical layout on device:

```text
~/homebrew/plugins/decky-secrets/
  decky_secrets/
  dist/
  main.py
  plugin.json
  package.json
```

The bundled Python package directory must ship beside `main.py`. Decky Loader may import `main.py` from the plugin sandbox without first placing the plugin root on `sys.path`, so `main.py` now bootstraps its own plugin-root import path before importing `decky_secrets`.

If you are developing from another machine, `rsync` or `scp` the repository contents over after building.

After copying the plugin files onto the device:

1. restart Decky Loader
2. open the Decky sidebar
3. open **Decky Secrets**

## Verify

For the current scaffold plus persistence/auth/Decky UI slices, verify the following:

1. `pnpm install` succeeds on a fresh checkout
2. `pnpm build` produces `dist/index.js`
3. `python3 -m unittest tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli tests.test_plugin` passes
4. `python3 -m unittest tests.test_import_layout` proves `main.py` can import `decky_secrets` even when loaded from a file path outside the repo-root `sys.path` assumption
5. `pnpm test:frontend` passes
6. `python3 -m decky_secrets list` shows non-secret record fields only after successful master-password and PIN auth in the current invocation
7. Decky Loader shows the `Decky Secrets` plugin in the sidebar
8. opening the plugin renders the first-run, full-lock, session-lock, and accessible screens successfully
9. when backend state is `session_locked`, the first visible UI is the numeric PIN pad, a correct PIN unlocks immediately on the final required digit, and a wrong PIN produces an unmistakable visible failure cue
10. routine list browsing and record detail navigation do not echo secret values in list/detail payloads until an explicit reveal or copy action is taken
11. the unlocked list keeps password copy as the default row action and exposes record detail through a dedicated trailing details affordance
12. record detail keeps the password masked by default and re-masks when the press-and-hold reveal stops
13. add, edit, and delete flows succeed through the backend validation/auth boundary and surface duplicate/missing-record failures without exposing secret values
14. visible UI wording distinguishes session lock from restart or full relock so first-use Decky users are told that master password is required again after restart or full relock
15. when backend state is `accessible`, using the record copy action shows copy confirmation plus the timeout cue without echoing the secret value
16. the UI describes clipboard clearing as best effort rather than a guaranteed wipe
17. fresh copy, reveal, edit, and delete actions are blocked when backend state is `decrypt_required` or `session_locked`
18. CLI invalid usage, duplicate keys, missing keys, auth failures, and prompt-unavailable failures exit non-zero with clear non-secret messages
19. a backend-created vault file remains encrypted at rest and is not readable as plaintext JSON secret data
20. backend timeout and restart tests prove the session window expires back to `session_locked` and the full relock path returns to `decrypt_required`

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
