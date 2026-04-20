## Summary
- add a local CLI entry point at `python3 -m decky_secrets` with the scoped MVP commands `add`, `list`, `rm`, and `update`
- keep the CLI on the shared backend auth boundary by prompting for master password and PIN through the existing auth manager before vault access, with docs/tests explicitly reflecting the shipped one-shot process model
- support `--secret` and `--secret-stdin`, reject conflicting secret-input flags, and keep list/output/error paths free of secret-bearing values
- document the CLI usage, one-shot auth behavior, and conservative `/dev/tty` prompting behavior in the README and durable project docs

## Testing
- python3 -m unittest tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli
- python3 -m py_compile main.py decky_secrets/vault.py decky_secrets/auth.py decky_secrets/clipboard.py decky_secrets/cli.py decky_secrets/__main__.py
- node --test tests/clipboard-flow.test.mjs
- corepack pnpm build
- python3 -m decky_secrets --help
- /data/.openclaw/workspace/tmp/agentic-team-plugin/.active/framework/scripts/validate-readme-contract.sh /data/.openclaw/workspace-builder-decky-secrets/repo

## Scope notes
- keeps CLI scope limited to `add`, `list`, `rm`, and `update`
- does not absorb Decky UI record-management work, clipboard changes, or backend auth redesign
- keeps auth prompting interactive-first and fails cleanly when a secure prompt path is unavailable
- makes the one-shot CLI auth model explicit instead of overstating cross-invocation session-lock reuse
