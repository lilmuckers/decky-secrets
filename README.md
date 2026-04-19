# decky-secrets

A Decky Loader plugin for Steam Deck / SteamOS that will eventually store user secrets locally in an encrypted vault and make them easy to copy during a running gaming session.

## Current status

Issue #3 adds only the initial Decky plugin skeleton.

What exists now:
- Decky plugin metadata in `plugin.json`
- a TypeScript frontend scaffold in `src/index.tsx`
- a minimal Python backend entrypoint in `main.py`
- Rollup and TypeScript build config for the current Decky template toolchain
- a placeholder Decky panel that loads and shows scaffold status
- a reserved `backend/` directory for later vault/backend implementation work

What is intentionally **not** implemented yet:
- vault persistence
- cryptography
- password unlock flow
- PIN unlock flow
- clipboard copy or wipe behavior
- CLI ingest or record management

## Repository layout

```text
.
├── backend/           # reserved for future backend build artifacts/source
├── docs/              # spec, architecture, decisions, delivery state
├── main.py            # live Decky Python backend entrypoint
├── package.json       # frontend toolchain config
├── plugin.json        # Decky plugin metadata
├── rollup.config.js   # Decky Rollup build config
├── src/index.tsx      # placeholder Decky sidebar UI
└── tsconfig.json      # TypeScript compiler settings
```

The scaffold keeps room for the documented Python-owned vault model and the distinct lock states defined in `SPEC.md` and `docs/spec-wiki-architecture.md`.

## Local development

### Install prerequisites

For the current Decky template toolchain, install:
- Node.js 16.14 or newer
- `pnpm` 9.x
- Decky Loader on the target Steam Deck / SteamOS device

Example:

```bash
npm install -g pnpm@9
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

For this scaffold slice, verify the following:

1. `pnpm install` succeeds on a fresh checkout
2. `pnpm build` produces `dist/index.js`
3. Decky Loader shows the `Decky Secrets` plugin in the sidebar
4. opening the plugin renders the placeholder panel successfully
5. the panel shows the placeholder backend state `uninitialized_vault`
6. the panel renders the reserved MVP screen note without crashing

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
