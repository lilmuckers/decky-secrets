# decky-secrets

A Decky Loader plugin for Steam Deck / SteamOS that will eventually store user secrets locally in an encrypted vault and make them easy to copy during a running gaming session.

## Current status

Issues #3 and #4 establish the initial Decky plugin scaffold plus the Python encrypted-vault persistence layer.

What exists now:
- Decky plugin metadata in `plugin.json`
- a TypeScript frontend scaffold in `src/index.tsx`
- a Python backend entrypoint in `main.py`
- a testable Python vault module in `decky_secrets/vault.py`
- Rollup and TypeScript build config for the current Decky template toolchain
- a placeholder Decky panel that loads and shows backend status
- encrypted-at-rest vault creation and load support at `~/.decky-secrets/vault`
- unit tests for blob shape, permissions, and password-based decrypt

What is intentionally **not** implemented yet:
- password unlock flow orchestration
- PIN unlock/session-lock flow orchestration
- clipboard copy or wipe behavior
- Decky record-management UI flows
- CLI ingest or broader record-management commands

## Repository layout

```text
.
├── backend/              # reserved for future backend build artifacts/source
├── decky_secrets/        # Python vault persistence and crypto module
├── docs/                 # spec, architecture, decisions, delivery state
├── main.py               # live Decky Python backend entrypoint
├── package.json          # frontend toolchain config
├── plugin.json           # Decky plugin metadata
├── requirements.txt      # Python backend dependency pinning
├── rollup.config.js      # Decky Rollup build config
├── src/index.tsx         # placeholder Decky sidebar UI
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

For the current scaffold plus persistence slice, verify the following:

1. `pnpm install` succeeds on a fresh checkout
2. `pnpm build` produces `dist/index.js`
3. `python3 -m unittest tests.test_vault` passes
4. Decky Loader shows the `Decky Secrets` plugin in the sidebar
5. opening the plugin renders the placeholder panel successfully
6. the panel shows either `uninitialized_vault` or `decrypt_required`, depending on whether `~/.decky-secrets/vault` already exists
7. a backend-created vault file remains encrypted at rest and is not readable as plaintext JSON secret data

## Product direction

The target MVP remains:
- local encrypted secret storage at `~/.decky-secrets/vault`
- password-first decrypt after boot and after full relock
- required PIN-gated session access
- Decky UI for browsing and managing records
- local CLI support for technical users

For the authoritative product and architecture definition, see:
- `SPEC.md`
- `docs/spec-wiki-home.md`
- `docs/spec-wiki-architecture.md`
- `docs/spec-wiki-assumptions-and-decisions.md`
- `docs/decisions/2026-04-18-vault-security-baseline.md`
