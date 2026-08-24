# Architecture Decision Records

Use this directory for durable architectural decisions that affect the Hermes ↔ ChatGPT product.

## Rules

- One decision per file.
- Number files sequentially: `0001-...md`, `0002-...md`, etc.
- Record context, decision, consequences, and status.
- Do not use ADRs for short-lived implementation notes.
- If a decision changes, add a new ADR that supersedes the prior one rather than silently rewriting history.

## Accepted decisions

- [`0001-shared-control-plane.md`](0001-shared-control-plane.md)
- [`0002-private-public-convergence.md`](0002-private-public-convergence.md)
- [`0003-hermes-http-sse-runtime-boundary.md`](0003-hermes-http-sse-runtime-boundary.md)
