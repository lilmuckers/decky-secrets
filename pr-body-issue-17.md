## Summary
- fix the packaged Decky backend import path so `main.py` can import the bundled `decky_secrets` package inside the real plugin sandbox
- add a package-level smoke test that loads `main.py` from a file path without the repo root on `sys.path`, matching the failing Decky runtime assumption more closely
- document the shipped plugin layout requirement that `decky_secrets/` lives beside `main.py` and that the backend bootstrap owns making that path importable

## Testing
- `python3 -m unittest tests.test_import_layout tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli tests.test_plugin`
- `python3 -m py_compile main.py decky_secrets/vault.py decky_secrets/auth.py decky_secrets/clipboard.py decky_secrets/cli.py decky_secrets/__main__.py`
- repo-local import smoke test that loads `main.py` via `importlib.util.spec_from_file_location(...)` with the repo root removed from `sys.path`
- `node --test tests/clipboard-flow.test.mjs tests/ui-flow.test.mjs tests/ui-contract.test.mjs`
- `corepack pnpm build`
- README contract validation

## Scope notes
- this slice fixes only Decky packaged Python import/layout compatibility
- it does not attempt to solve the later Steam Deck `cryptography` / OpenSSL runtime compatibility issue
- real Steam Deck confirmation is still required in review to close the issue fully
