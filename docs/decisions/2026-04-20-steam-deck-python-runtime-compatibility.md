# Decision: Steam Deck Python runtime compatibility is a ship gate

- Status: accepted
- Date: 2026-04-20
- Owner: Spec

## Context
Real on-device testing after the MVP issue run exposed runtime failures that were not visible in local or CI validation. The first packaged backend failed inside the Decky plugin sandbox with `ModuleNotFoundError: No module named 'decky_secrets'` from `main.py`. After import-path correction, the secure backend then failed on device while importing `cryptography` because the packaged binary expected `OPENSSL_3.2.0`, which was not available in the Steam Deck runtime. A temporary compatibility build that bypassed the incompatible secure dependency stack still loaded, which confirmed that the Decky plugin shell and UI path were viable and that the principal blocker was Python backend/runtime compatibility on the real target device.

## Decision
The project adopts the following constraints for all backend-affecting work on Steam Deck:

1. **Real Steam Deck validation is a release gate**
   - Backend-affecting work is not complete until the packaged plugin is smoke-tested on a real Steam Deck through Decky Loader.
   - At minimum, that validation must prove backend import resolution and secure backend startup on device.

2. **Decky sandbox import compatibility is part of the product contract**
   - Bundled Python code must be packaged so `main.py` can import the backend package correctly inside the Decky plugin sandbox.
   - Import-path assumptions that work only in local development or CI are not sufficient.

3. **The security baseline stays fixed, but the crypto implementation library does not**
   - The MVP still requires AES-256-GCM vault encryption and PBKDF2-SHA-256 with the approved iteration counts.
   - The shipped backend may use any vetted implementation that preserves that security profile and actually runs on the target Steam Deck runtime.
   - A packaged binary dependency that requires an unavailable OpenSSL ABI on device is not acceptable as the shipped secure backend path.

4. **Compatibility should be solved without weakening the security posture**
   - The right fix is either a Steam Deck compatible packaging/runtime strategy or a reduced dependency surface that still preserves the approved crypto profile.
   - The project should not respond to the current packaging failure by weakening the encryption model, removing the password/PIN architecture, or lowering the documented crypto claims.

## Consequences
- Follow-up work should be split into explicit delivery slices for import-path compatibility and secure crypto-runtime compatibility.
- Issues that touch backend packaging or secure backend startup must include real-device Steam Deck validation in acceptance criteria.
- The earlier assumption that the initial packaged `cryptography` path would run cleanly on the target device is now treated as disproved.
- UI polish can follow later; the immediate priority is making the secure Python backend shippable on Steam Deck.
