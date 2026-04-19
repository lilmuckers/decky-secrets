# Backend placeholder

This directory is intentionally present to preserve the standard Decky plugin layout for future backend build work.

For this scaffold slice:
- `main.py` remains the live Python backend entrypoint expected by Decky Loader
- no vault persistence, crypto, CLI, or lock-state enforcement lives here yet
- future issues can add `backend/src/` and `backend/out/` content without restructuring the plugin root
