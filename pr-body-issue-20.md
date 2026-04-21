## Summary
- add a GitHub Actions workflow that builds the Decky plugin, validates the current backend/frontend/package path, and uploads a Decky Loader friendly zip artifact from the workflow run
- add an explicit packaging script so the zip contents are defined in one place and can be validated locally outside GitHub Actions
- document the package contract clearly, including which runtime files are shipped and which repository-only files are excluded

## Testing
- `python3 -m unittest tests.test_import_layout tests.test_package_plugin tests.test_vault tests.test_auth tests.test_clipboard tests.test_cli tests.test_plugin`
- `python3 -m py_compile main.py decky_secrets/vault.py decky_secrets/auth.py decky_secrets/clipboard.py decky_secrets/cli.py decky_secrets/__main__.py`
- `node --test tests/clipboard-flow.test.mjs tests/ui-flow.test.mjs tests/ui-contract.test.mjs`
- `corepack pnpm build`
- `python3 scripts/package_plugin.py --repo-root . --out-dir build/package`
- inspect `build/package/decky-secrets.zip` and `build/package/decky-secrets-manifest.json`
- README contract validation

## Scope notes
- this slice adds GitHub Actions build/package automation and workflow-visible artifacts only
- it does not implement release tagging or GitHub Release publication
- it keeps the current Steam Deck runtime compatibility constraints in mind by validating the existing backend import path and packaging boundary without redesigning runtime strategy
