# Release Requirements

This is the product-level readiness checklist for M5/M6. It does not replace platform-specific submission requirements, which must be re-verified when submission begins.

## Core user journeys

A release candidate should support these flows end to end:

1. Connect/authenticate the user's supported Hermes/Nous environment.
2. List or resolve available Hermes agents/runtimes.
3. Create/start a supported agent/runtime when permitted.
4. Delegate a task.
5. Inspect task status and final result.
6. Continue the same session/task context.
7. Approve/deny pending consequential actions where supported.
8. Cancel work and safely stop/destroy resources when permitted.

## Security

- Production authentication configured.
- Tenant isolation verified with negative tests.
- Secrets encrypted/stored server-side.
- No raw credentials in logs, prompts, tool outputs, source, issues, or docs.
- Authorization enforced server-side.
- Destructive actions have explicit policy/approval behavior.
- Raw Hermes runtime is not unnecessarily exposed publicly.

## Reliability

- Idempotency/retry behavior defined for mutation operations.
- Runtime disconnect/reconnect behavior tested.
- Timeouts and cancellation tested.
- Duplicate task submission behavior understood.
- Runtime-unavailable behavior produces normalized errors.
- Long-running task state survives client request boundaries.

## Observability

Operators can determine, without exposing secrets:

- who invoked a task,
- which tenant/runtime handled it,
- current/final task state,
- important lifecycle operations,
- why failures occurred,
- relevant usage/cost metadata where available.

## UX

- First-run path is understandable without Hermes/MCP knowledge.
- Empty/loading/error states are clear.
- Status language maps to actual server state.
- Users can understand when approval is required.
- Mobile-sized surfaces remain usable where the ChatGPT platform supports the app.

## Publication package

Re-verify current platform requirements before submission. Expect to need the applicable combination of:

- public HTTPS MCP/app endpoint,
- production OAuth configuration,
- verified domains,
- plugin/app manifest and technical IDs,
- app name/description/prompts/assets,
- privacy policy,
- support/contact information,
- data handling/retention disclosures,
- positive and negative test cases,
- review instructions.

## Release rule

Do not treat publication approval as proof of runtime correctness. M5 end-to-end/security gates must be independently satisfied before M6 is considered complete.
