---
name: Spec Approval Gate
about: Designates the spec-approval gate issue for this project. Orchestrator stays in guided mode until this issue is closed by the human operator.
title: "spec-approval: <project name>"
labels: spec-approval
assignees: ''
---

## Purpose

This issue is the spec-approval gate for this project.

While this issue is **open**, the Orchestrator operates in **guided mode**:
- work may be dispatched to Spec and Builder
- but merge and release decisions require human confirmation

When the human operator closes this issue, the Orchestrator may proceed in **autonomous delivery mode**.

## Spec approval checklist

- [ ] `SPEC.md` reflects the agreed project definition
- [ ] wiki pages are created and linked
- [ ] initial backlog issues are created and scoped
- [ ] acceptance criteria are visible and buildable
- [ ] Orchestrator has been briefed on the approved delivery scope

## Instructions for the operator

Close this issue when you are satisfied that:
1. the project spec is correct
2. the initial issues are ready to build
3. the swarm is correctly configured

Do not close this issue to unblock a stuck run — only close it when spec-level approval has genuinely been given.
