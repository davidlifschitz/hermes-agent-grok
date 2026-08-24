# Publish Path — Stable Product

## Purpose

Turn the shared Hermes Control Plane into a secure, understandable, multi-user ChatGPT product that can be distributed through the supported ChatGPT app/plugin pathway.

## Product requirements

- production OAuth/resource-server authentication,
- user/tenant isolation,
- durable encrypted secrets handling,
- production persistence,
- polished onboarding and error UX,
- accurate tool annotations and approval semantics,
- reliability/reconnect/retry/idempotency behavior,
- audit and observability,
- rate limits/quotas/cost controls where required,
- privacy, retention, support, and submission documentation.

## Critical rule

The published product does not get a second implementation of Hermes control logic.

It calls the same shared task/session/runtime/policy services proven by the private channel.

## Convergence

M4 is complete only when private/canary and public/stable clients share the same backend implementation and automated behavioral tests.

## Publication readiness

See [`release-requirements.md`](release-requirements.md) and the M5/M6 gates in [`ROADMAP.md`](../../ROADMAP.md).
