# Hermes for ChatGPT — Project Overview

This repository is the canonical source of truth for the Hermes ↔ ChatGPT product.

## End goal

Build a cloud-hosted, function-agnostic agent platform that can be invoked directly from ChatGPT on web, mobile, and desktop/Codex without requiring end users to understand MCP, tunnels, VPS hosting, or Hermes internals.

A user should eventually be able to say things such as:

- “@Hermes research these companies.”
- “@Hermes continue the session from yesterday.”
- “@Hermes show me my running agents.”
- “@Hermes stop the expensive one.”
- “@Hermes create an agent for this marketing task.”

The same backend should support both a private/dogfood pathway and the eventual published ChatGPT product.

## Product boundary

ChatGPT is a client, not the control plane.

The shared control plane owns:

- identity and tenant resolution,
- Hermes/Nous runtime routing,
- task and session state,
- authorization and approvals,
- credentials and secrets boundaries,
- audit and usage metadata,
- reliability and retries,
- public/private client contracts.

Hermes remains the execution/orchestration runtime behind a stable adapter.

## Final architecture

```text
ChatGPT web / mobile / desktop / Codex
                  |
                  | MCP / HTTPS
                  v
          Hermes Control Plane
          - auth / tenants
          - agent registry
          - task router
          - session manager
          - policy / approvals
          - audit / usage
             /        \
            /          \
   Nous Portal MCP    Hermes runtime
   lifecycle/fleet    prompt/session/events
```

Cloudflare is transport and edge infrastructure, not the agent control plane.

## Two delivery pathways

### Private pathway

Purpose: fast owner-only dogfooding, protocol validation, canary testing, and future staging.

Temporary infrastructure is allowed here only when it sits behind production-shaped interfaces.

### Publish pathway

Purpose: secure multi-user ChatGPT product with production OAuth, tenant isolation, polished UX, reliability, and publication requirements.

### Convergence rule

The private and publish pathways must converge on one shared backend at milestone M4. Do not build separate business logic for each pathway.

## Current milestone

**M1 — Hermes Remote Control**

M1 is not complete. The immediate job is to verify the real Hermes remote-control surface and implement the shared runtime/control-plane boundary.

See [`STATE.md`](STATE.md) for verified current status.

## Next three priorities

1. Verify the actual supported Hermes remote runtime/session protocol instead of relying on assumptions in older plans.
2. Implement the shared Hermes runtime adapter and Nous Portal lifecycle adapter.
3. Prove the first programmatic end-to-end flow: resolve/start Hermes → submit task → observe result → stop/reuse runtime.

## Hard development rules

1. One shared core; private and public clients stay thin.
2. Every substantial change maps to a roadmap milestone.
3. Do not introduce a private-only architecture that must later be rewritten for publication.
4. Hermes and Nous are integrations behind interfaces, not the product architecture itself.
5. Long-running task/session state lives server-side.
6. Credentials must never transit model context or be committed to the repository.
7. Missing runtime capabilities must fail explicitly; never fabricate support.
8. A feature is not complete until the relevant end-to-end path is verified.
9. Update `STATE.md` whenever verified project state materially changes.
10. Architectural changes require an ADR under `docs/decisions/`.

## Canonical documents

Read these in order before substantive project work:

1. [`PROJECT.md`](PROJECT.md) — what we are building and why.
2. [`STATE.md`](STATE.md) — verified reality today.
3. [`ROADMAP.md`](ROADMAP.md) — milestone sequence and gates.
4. [`ARCHITECTURE.md`](ARCHITECTURE.md) — long-lived architecture and invariants.
5. [`docs/decisions/`](docs/decisions/) — accepted architecture decisions.
6. Existing detailed specs/plans under `docs/superpowers/` — implementation detail and historical design work.

If documents disagree, prefer verified code/current behavior, then `STATE.md`, then accepted ADRs/architecture, then roadmap/spec/planning documents.

## Repository role

GitHub is the durable project brain across ChatGPT web/mobile, Codex, and local development. Conversation history and memory are useful context, but they are not authoritative project state.
