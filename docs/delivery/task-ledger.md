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
