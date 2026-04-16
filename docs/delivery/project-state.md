# Project State

This file records the activation state of the project.
It is the canonical artifact for project-activation gate checks.

See the framework's `policies/project-activation.md` for the full contract.

## Current State

```json
{
  "project": "decky-secrets",
  "state": "BOOTSTRAPPED",
  "bootstrapped_at": "2026-04-16T21:45:39Z",
  "defined_at": null,
  "activated_at": null,
  "spec_approval_ref": null,
  "activated_by": null,
  "notes": [
    "Framework bootstrap completed locally on 2026-04-16.",
    "Initial project intent captured from Patrick's startup brief.",
    "Project remains BOOTSTRAPPED until wiki, backlog, and spec approval gate are in place."
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