# ADR 0001 — Shared Control Plane

**Status:** Accepted  
**Date:** 2026-08-24

## Context

The product needs to support ChatGPT web/mobile/desktop/Codex clients while controlling Hermes runtimes that may be private/BYO or managed. Putting runtime state, credentials, or orchestration logic directly in a ChatGPT client would create fragile client-specific implementations and make publication/security harder.

## Decision

Use one server-side Hermes Control Plane as the product core.

The control plane owns identity, tenant resolution, runtime routing, tasks, sessions, policy, approvals, persistence, audit/usage metadata, and reliability behavior.

ChatGPT clients remain thin MCP/HTTPS clients. Hermes and Nous Portal are accessed through adapters behind the control plane.

## Consequences

### Positive

- Web/mobile/desktop clients share the same backend behavior.
- Long-running tasks survive client/tool-call boundaries.
- Credentials remain server-side.
- Private dogfood work directly hardens the future product.
- Additional agent harnesses can later fit behind runtime adapters without redesigning ChatGPT-facing contracts.

### Costs

- Requires a persistent backend rather than a purely client-side/plugin-only design.
- Requires explicit task/session persistence and authorization.
- Runtime connection/recovery logic becomes a platform responsibility.

## Guardrail

Do not add Hermes business logic directly to private or public ChatGPT client adapters when it belongs in the shared service.
