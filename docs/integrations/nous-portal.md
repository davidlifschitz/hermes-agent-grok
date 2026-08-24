# Nous Portal Integration

## Role

Nous Portal is an external identity/account and Hermes Cloud lifecycle/tool integration. It is not the Hermes for ChatGPT control plane.

## Intended responsibilities

Where supported and verified, the shared control plane may use Portal for:

- OAuth/account and organization context,
- listing Hermes Cloud agents/runtimes,
- status/cost metadata,
- create/start/stop/restart/destroy lifecycle actions,
- hosted model/tool access associated with the user's Nous account.

## Boundary

Portal access belongs behind a `NousPortal`/lifecycle adapter. ChatGPT-facing tools should call the shared domain service rather than invoking Portal MCP semantics directly.

## Security

- Portal credentials/tokens stay server-side.
- Never commit tokens or place them in model context.
- Tenant/org identity must be derived from authenticated state.

## Current state

See [`STATE.md`](../../STATE.md). Live account/OAuth state must be re-verified before being marked operational.
