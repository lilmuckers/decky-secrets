# Project State

This file records the activation state of the project.
It is the canonical artifact for project-activation gate checks.

See the framework's `policies/project-activation.md` for the full contract.

## Current State

```json
{
  "project": "decky-secrets",
  "state": "ACTIVE",
  "bootstrapped_at": "2026-04-16T21:45:39Z",
  "defined_at": "2026-04-19T09:15:10Z",
  "activated_at": "2026-04-19T09:15:10Z",
  "spec_approval_ref": "https://github.com/lilmuckers/decky-secrets/issues/1",
  "activated_by": "Patrick",
  "notes": [
    "Framework bootstrap completed locally on 2026-04-16.",
    "Initial project intent captured from Patrick's startup brief.",
    "Definition readiness was verified across spec, wiki, design docs, and implementation backlog before activation.",
    "Spec approval issue #1 was closed by the human on 2026-04-19, activating normal Builder dispatch."
  ]
}
```

## State Transitions

| State | Meaning |
|-------|---------|
| `BOOTSTRAPPED` | Infra exists: agents, workspaces, repo templates, smoke test passed. No spec or backlog yet. |
| `DEFINED` | Spec, wiki, backlog, and ready issues exist. Awaiting human approval before build work begins. |
| `ACTIVE` | Human approved spec/backlog. Orchestrator may dispatch Builder to ready issues. |

## Transition Rules

- **BOOTSTRAPPED → DEFINED**: Spec completes initial SPEC.md, wiki page, and backlog. Orchestrator verifies conditions and updates state.
- **DEFINED → ACTIVE**: Human closes the `spec-approval` issue. Orchestrator records activation immediately.
- Builder must not begin normal implementation unless state is `ACTIVE`.
- Orchestrator must not dispatch normal build work unless state is `ACTIVE`.
- Run `scripts/validate-project-activation.sh <project> <repo-path>` to verify current state at any point.