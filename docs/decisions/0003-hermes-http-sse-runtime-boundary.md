# ADR 0003 — Hermes HTTP/SSE Runtime Boundary

**Status:** Accepted  
**Date:** 2026-08-24

## Context

The original product plan assumed a complete `/v1/runs` lifecycle in files that
do not exist. Audit found an HTTP adapter under `gateway/platforms`, but its run
surface is limited to submission and a one-shot in-memory SSE stream. It has no
durable run lookup, replay, cancellation, continuation proof, or approvals.

## Decision

Use a transport-neutral shared runtime adapter that wraps only verified Hermes
HTTP behavior: health, run submission, and terminal observation over SSE.
Unsupported operations remain in the stable capability vocabulary and fail with
a typed `UNSUPPORTED_CAPABILITY` error.

Keep durable product tasks outside the runtime adapter. A control-plane task
service will own tenant-scoped product IDs, consume runtime events, and persist
status/results. Hermes runtime IDs are routing metadata, never authorization.
Nous Portal lifecycle is a separate adapter and does not define task/session
models.

## Consequences

- The first implementation proves the available M1 wire lifecycle without
  fabricating status, cancellation, continuation, or approvals.
- ChatGPT/private clients cannot be the only SSE consumer, preserving the M4
  shared-backend direction.
- Control-plane restart recovery remains limited until Hermes adds durable run
  query/replay; interrupted tasks must become explicitly unknown rather than be
  guessed complete or failed.
- Runtime-hop bearer authentication is not product identity or tenant auth.

