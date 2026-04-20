## Summary
- implement the MVP Decky record-management UI flows for first run, full lock, session lock, unlocked list, record detail, and add/edit/delete actions
- keep routine list browsing and detail payloads non-secret while reserving plaintext secret delivery for explicit reveal and copy actions
- align the Decky PIN pad, press-and-hold reveal, and backend-authoritative lock-state handling with the approved issue #9 security contract

## Testing
- `python3 -m unittest tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli tests.test_plugin`
- `python3 -m py_compile main.py decky_secrets/vault.py decky_secrets/auth.py decky_secrets/clipboard.py decky_secrets/cli.py decky_secrets/__main__.py`
- `node --test tests/clipboard-flow.test.mjs tests/ui-flow.test.mjs`
- `corepack pnpm build`
- `/data/.openclaw/workspace/tmp/agentic-team-plugin/.active/framework/scripts/validate-readme-contract.sh /data/.openclaw/workspace-builder-decky-secrets/repo`

## Scope notes
- consumes the existing vault, auth, and clipboard backend contracts from issues #4, #5, and #7
- keeps copy wording best-effort only and does not redesign clipboard timers, CLI auth, or backend auth behavior
- uses explicit reveal-on-hold in record detail and dedicated details navigation instead of exposing secrets during routine list browsing
