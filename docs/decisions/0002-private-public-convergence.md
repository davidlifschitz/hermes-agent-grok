# ADR 0002 — Private and Public Convergence

**Status:** Accepted  
**Date:** 2026-08-24

## Context

The project needs a fast private pathway for owner dogfooding before the public ChatGPT product is ready. A separate private architecture would accelerate the first demo but create migration debt and risk a rewrite when OAuth, tenancy, publication, and multi-user requirements arrive.

## Decision

Treat private and published access as two delivery channels over one product architecture.

The private path may temporarily use simpler authentication, ingress, persistence, or deployment configuration, but these differences must remain behind shared interfaces.

At roadmap milestone M4, private/canary and public/stable clients must use the same control-plane implementation and domain contracts.

## Consequences

### Positive

- Private testing validates code that will actually ship.
- Protocol/reliability issues found early improve the public product directly.
- Fewer duplicate implementations and fewer migration projects.
- Private access remains useful after launch as canary/staging/admin infrastructure.

### Costs

- Early code must honor production-shaped boundaries even when only one owner exists.
- Some shortcuts that would make a one-off private bridge faster are intentionally rejected.

## Guardrail

A private-only implementation is acceptable only when its replaceable portion is configuration/infrastructure. Do not fork core task, session, runtime, authorization, or tool behavior between private and public pathways.
