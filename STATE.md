# Hermes for ChatGPT — Current State

**Last verified:** 2026-08-24

This file records verified project reality, not aspirations. Update it whenever code, deployment, authentication, or end-to-end capability materially changes.

## Current milestone

**M1 — Hermes Remote Control**

Status: **in progress / not complete**.

## Verified present in the repository

- The repository is a Hermes Agent fork with the upstream agent/runtime/CLI/gateway codebase.
- `AGENTS.md` documents the existing Hermes codebase and development conventions.
- A product architecture spec exists at:
  - `docs/superpowers/specs/2026-08-23-chatgpt-hermes-app-design.md`
- That spec defines:
  - a ChatGPT-facing control plane,
  - BYO and managed Hermes modes,
  - OAuth/MCP boundaries,
  - tenant/policy concepts,
  - `run/status/continue/result/approve/cancel` style operations.
- An implementation-plan branch exists:
  - `feature/chatgpt-hermes-gateway-v1`
- That branch currently contains a detailed implementation plan rather than the planned gateway package implementation.

## Verified not yet implemented as project-specific product code

The current audit did not find the planned shared product implementation under paths such as:

```text
apps/hermes-chatgpt-gateway/
plugins/hermes/
```

The following product capabilities are therefore not yet considered complete:

- shared Hermes Control Plane implementation,
- Hermes runtime adapter used by the ChatGPT product,
- Nous Portal lifecycle adapter used by the shared control plane,
- persistent task/session service for ChatGPT delegation,
- ChatGPT-facing MCP gateway implementation,
- private ChatGPT ↔ Hermes end-to-end connection,
- production OAuth/tenant isolation,
- Cloudflare/private ingress deployment for the product gateway,
- public Apps SDK/plugin packaging and submission path,
- private/public convergence on a deployed backend.

## Important discrepancy to resolve before implementation

The existing `feature/chatgpt-hermes-gateway-v1` implementation plan states that the fork already exposes an API-server surface such as `/v1/runs` and references an existing Hermes API server as the first runtime adapter target.

During the 2026-08-24 repo audit, exact referenced files such as:

```text
hermes_cli/api_server.py
hermes_cli/api_app.py
```

were not present on `main` and exact file fetches returned 404.

**Consequence:** do not implement the runtime adapter from that assumption alone. First verify the actual current Hermes remote-control surface (`hermes serve`, gateway/runtime modules, or another supported interface) and update the implementation plan accordingly.

## Current architectural decisions

- GitHub is the canonical project brain.
- ChatGPT is a client, not the control plane.
- Private and public delivery paths must share one backend.
- Private infrastructure may be temporary, but only behind production-shaped interfaces.
- Hermes/Nous are integrations behind adapter boundaries.
- Long-running work should use durable server-side task/session identifiers.
- Credentials must remain outside model context and repository content.

## Immediate next actions

1. Inspect and verify the actual current Hermes remote runtime/session interface.
2. Reconcile the V1 implementation plan with verified Hermes capabilities.
3. Implement the shared runtime adapter/control-plane foundation.
4. Prove a programmatic Hermes task lifecycle before building further product UX.

## Blockers / unverified external state

Do not mark these as complete in this file until re-verified through the relevant live environment:

- live Nous Portal OAuth/account state,
- Hermes Cloud discovery/connectivity from the deployment environment,
- persistent public/private gateway hosting,
- Cloudflare route/tunnel configuration,
- ChatGPT developer-mode/private MCP write capability for the active account,
- public plugin/app registration or review status.

## How to update this file

When a change lands, record only evidence-backed state. Prefer wording such as:

- `Verified working:` followed by the test/endpoint/path.
- `Verified failing:` followed by the observed error.
- `Unverified:` when an external or account-dependent step has not been exercised.

Do not copy future-tense implementation-plan statements into this file as if they already exist.
