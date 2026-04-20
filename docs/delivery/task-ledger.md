# Task Ledger

This ledger is the Orchestrator's durable record of in-flight delegated work.
It is the sole persistence mechanism for task state across agent sessions.

## Operating Rules

- Each task entry must use a level-2 heading in the form `## Task <task-id> - <title>`.
- Each task entry must contain exactly one fenced `json` block.
- The JSON payload is the machine-updatable source of truth for task state.
- Human notes belong outside the JSON block only when they add context the payload does not carry.

## Required JSON Fields

- `task`
- `state`
- `current_action`
- `next_action`
- `history`

## Optional Operational Fields

- `owner` — the named agent currently accountable for the task
- `branch` — active implementation branch (set by Orchestrator when Builder starts)
- `pr` — GitHub PR number or URL (set when Builder raises the PR)
- `expected_callback_at` — ISO-8601 timestamp used by the OpenClaw watchdog cron to detect overdue callbacks

## Allowed States

- `queued`
- `in_progress`
- `blocked`
- `needs_review`
- `done`

## Entry Template

```

## Task TASK-ID - Short title

```json
{
  "task": "TASK-ID",
  "state": "queued",
  "current_action": "Describe what is happening now",
  "next_action": "Describe the next expected transition",
  "owner": "orchestrator-<project>",
  "branch": null,
  "pr": null,
  "expected_callback_at": null,
  "history": [
    {
      "at": "2026-01-01T00:00:00Z",
      "action": "Task created",
      "by": "orchestrator-<project>"
    }
  ]
}
```
```
## Task ISSUE-3 - Create initial Decky Loader plugin skeleton

```json
{
  "task": "ISSUE-3",
  "state": "done",
  "current_action": "PR #10 merged and issue #3 completed.",
  "next_action": "No further action on issue #3. Identify or prepare the next ready issue before dispatching Builder again.",
  "owner": "orchestrator-decky-secrets",
  "expected_callback_at": "2026-04-19T11:45:00Z",
  "history": [
    {
      "at": "2026-04-19T09:32:01Z",
      "action": "Dispatched issue #3 to Builder after readiness validation passed",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T09:38:52Z",
      "action": "Builder reported NEEDS_REVIEW with PR #10 for issue #3",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T09:42:30Z",
      "action": "QA reported DONE and applied qa-approved for PR #10",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T09:45:14Z",
      "action": "Spec reported DONE and applied spec-satisfied for PR #10",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T09:46:20Z",
      "action": "Merged PR #10 and completed issue #3",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task ISSUE-6 - Threat-model clipboard, lock-state, and local secret exposure risks

```json
{
  "task": "ISSUE-6",
  "state": "done",
  "current_action": "PR #11 merged and issue #6 completed.",
  "next_action": "Use the new security-boundary decision doc and aligned architecture/assumptions pages as the durable reference for issues #4, #5, #7, and #9.",
  "owner": "orchestrator-decky-secrets",
  "expected_callback_at": "2026-04-19T21:20:00Z",
  "history": [
    {
      "at": "2026-04-19T18:51:00Z",
      "action": "Dispatched issue #6 to Security for security-boundary definition",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T18:59:22Z",
      "action": "Security reported NEEDS_REVIEW with PR #11 for issue #6",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T19:00:39Z",
      "action": "Spec reported DONE and applied spec-satisfied for PR #11",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T19:01:26Z",
      "action": "Dispatched PR #11 to QA after merge gate reported missing qa-approved",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T19:03:19Z",
      "action": "QA reported DONE and applied qa-approved for PR #11",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T19:03:50Z",
      "action": "Merged PR #11 and completed issue #6",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task TASK-2026-04-19-issue-tightening - Tighten issues #4, #5, #7, and #9 against merged security boundaries

```json
{
  "task": "TASK-2026-04-19-issue-tightening",
  "state": "done",
  "current_action": "Spec completed the issue-tightening pass for issues #4, #5, #7, and #9 against the merged local secret exposure decision.",
  "next_action": "No further action needed on the tightening task; continue normal Builder dispatch with issue #7 next.",
  "owner": "orchestrator-decky-secrets",
  "expected_callback_at": "2026-04-19T21:30:00Z",
  "history": [
    {
      "at": "2026-04-19T19:13:50Z",
      "action": "Dispatched Spec to tighten implementation issues after issue #6 security-boundary merge",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T22:12:07Z",
      "action": "Spec reported DONE for the issue-tightening watchdog task",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task ISSUE-4 - Implement Python vault persistence and cryptography layer

```json
{
  "task": "ISSUE-4",
  "state": "done",
  "current_action": "PR #12 merged and issue #4 completed.",
  "next_action": "Continue planned sequencing with issue #7 as the next backend slice on top of the merged persistence layer.",
  "owner": "orchestrator-decky-secrets",
  "expected_callback_at": "2026-04-19T23:20:00Z",
  "history": [
    {
      "at": "2026-04-19T21:18:52Z",
      "action": "Resumed normal flow and dispatched issue #4 to Builder",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T21:25:07Z",
      "action": "Builder reported NEEDS_REVIEW with PR #12 for issue #4",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T21:26:55Z",
      "action": "Reset security workspace to main after stale-branch blocker and re-dispatched PR #12 security review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T21:29:07Z",
      "action": "QA and Security approved PR #12; dispatched to Spec for final review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T21:30:41Z",
      "action": "Spec reported DONE and applied spec-satisfied for PR #12",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-19T21:31:29Z",
      "action": "Merged PR #12 and completed issue #4",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task ISSUE-7 - Implement Python lock-state and authentication backend

```json
{
  "task": "ISSUE-7",
  "state": "done",
  "current_action": "PR #13 merged and issue #7 completed.",
  "next_action": "Use the merged lock/auth backend as the shared state boundary for subsequent UI and CLI slices, and ready issue #5 before the next Builder handoff.",
  "owner": "orchestrator-decky-secrets",
  "branch": "feat/issue-7-auth-backend",
  "pr": 13,
  "expected_callback_at": "2026-04-20T08:20:00Z",
  "history": [
    {
      "at": "2026-04-20T06:40:07Z",
      "action": "Dispatched Security to repair issue #7 readiness gaps before Builder handoff",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:43:49Z",
      "action": "Reset security workspace to main, synced to latest origin/main, and re-dispatched issue #7 readiness repair",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:47:16Z",
      "action": "Security completed issue #7 readiness repair; validation passed and Builder was dispatched",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:52:00Z",
      "action": "Builder reported NEEDS_REVIEW with PR #13 for issue #7; dispatched QA and Security review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:55:00Z",
      "action": "Security failed PR #13 with accessible-session and combined-failure deletion findings; re-dispatched Builder for rework",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:56:00Z",
      "action": "QA failed PR #13 on the same accessible-session defect and requested regression coverage for usable post-PIN accessible-session access",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T06:59:00Z",
      "action": "Builder updated PR #13 after rework; re-dispatched QA and Security for review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:02:00Z",
      "action": "QA and Security approvals are present on PR #13; dispatched Spec for final review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:05:00Z",
      "action": "Spec applied spec-satisfied on PR #13; orchestrator-approved applied and merge execution started",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:06:06Z",
      "action": "Merged PR #13 with merge commit 4e7923b199005882954bd67f2f5ec5b0f72f3179 and issue #7 closed",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task ISSUE-5 - Implement copy-to-pasteboard flow with timed clear

```json
{
  "task": "ISSUE-5",
  "state": "done",
  "current_action": "PR #14 merged and issue #5 completed.",
  "next_action": "Use the merged clipboard contract as fixed shared behavior and ready issue #8 before the next Builder handoff.",
  "owner": "orchestrator-decky-secrets",
  "branch": "feat/issue-5-clipboard-copy",
  "pr": 14,
  "expected_callback_at": "2026-04-20T11:05:00Z",
  "history": [
    {
      "at": "2026-04-20T07:08:00Z",
      "action": "Merged PR #13 completed issue #7; issue #5 was the next lowest-numbered ready-for-build issue, but validator failures routed it to Security for readiness repair before Builder handoff",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:10:00Z",
      "action": "Security completed issue #5 readiness repair; validation passed and Builder was dispatched",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:18:00Z",
      "action": "Builder reported NEEDS_REVIEW with PR #14 for issue #5; dispatched QA and Security review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:22:00Z",
      "action": "QA approved PR #14 and applied qa-approved; awaiting Security review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T07:23:00Z",
      "action": "Security blocked PR #14 on clipboard expiry handling across suspend/resume and Builder was re-dispatched for targeted rework",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T09:49:00Z",
      "action": "Resumed session, accepted Builder's timeout-boundary fix for PR #14, and re-dispatched Security review while preserving qa-approved",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T09:52:00Z",
      "action": "Security approved PR #14 and applied security-approved; dispatched Spec for final review",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T09:56:00Z",
      "action": "Spec applied spec-satisfied on PR #14; orchestrator-approved applied and merge execution started",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T09:57:47Z",
      "action": "Merged PR #14 with merge commit 7df0eaf29a2c4b923d80ddae529d29157f3a7cdb and issue #5 completed",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
## Task ISSUE-8 - Implement local CLI vault management commands

```json
{
  "task": "ISSUE-8",
  "state": "needs_review",
  "current_action": "Builder opened PR #15 for issue #8 and QA plus Security review are now in progress.",
  "next_action": "Await QA and Security callbacks for PR #15, then route to Spec if both pass.",
  "owner": "qa-decky-secrets",
  "branch": "feat/issue-8-cli-vault-commands",
  "pr": 15,
  "expected_callback_at": "2026-04-20T12:30:00Z",
  "history": [
    {
      "at": "2026-04-20T09:59:00Z",
      "action": "Merged PR #14 completed issue #5; issue #8 was the next lowest-numbered ready-for-build issue, but validator failures routed it to Spec for readiness repair before Builder handoff",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T10:01:00Z",
      "action": "Spec completed issue #8 readiness repair; validation passed and Builder was dispatched",
      "by": "orchestrator-decky-secrets"
    },
    {
      "at": "2026-04-20T10:08:00Z",
      "action": "Builder reported NEEDS_REVIEW with PR #15 for issue #8; dispatched QA and Security review",
      "by": "orchestrator-decky-secrets"
    }
  ]
}
```
