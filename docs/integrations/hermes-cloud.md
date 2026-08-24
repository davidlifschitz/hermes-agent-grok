# Hermes Cloud / Runtime Integration

## Role

Hermes is the execution/orchestration runtime. The ChatGPT product controls it through a stable runtime adapter rather than depending on internal agent-loop classes.

## Target runtime contract

```text
capabilities()
start_run(request)
get_run(run_id)
get_result(run_id)
continue_session(session_id, instruction)
approve(run_id, approval)
stop_run(run_id)
```

The exact transport may evolve. The domain contract should remain stable where possible.

## Verification requirement

Before implementing the adapter, verify the actual current supported Hermes remote-control/session surface. Do not rely solely on the older V1 plan's assumption of `/v1/runs` endpoints; the 2026-08-24 repo audit did not find the referenced `hermes_cli/api_server.py` or `hermes_cli/api_app.py` on `main`.

## Runtime behavior

The adapter is responsible for normalizing:

- runtime health/capabilities,
- run/task creation,
- status/events/results,
- session continuation,
- approvals where supported,
- cancellation where supported,
- unavailable/unsupported behavior.

## Current state

M1 is incomplete. See [`STATE.md`](../../STATE.md) for the current verified blockers and next actions.
