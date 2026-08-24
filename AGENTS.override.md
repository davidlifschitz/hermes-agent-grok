# Hermes for ChatGPT — Project Instructions

These instructions supplement the upstream Hermes development guide in `AGENTS.md`.

## Before substantive Hermes ↔ ChatGPT product work

Read, in order:

1. `PROJECT.md`
2. `STATE.md`
3. the relevant milestone in `ROADMAP.md`
4. `ARCHITECTURE.md`
5. relevant ADRs under `docs/decisions/`
6. relevant integration/product/implementation docs under `docs/`

Treat the repository as authoritative over conversation history or memory.

## Product development rules

- Every substantial product change must map to a roadmap milestone.
- Prefer shared-core changes over private/public client-specific business logic.
- Do not create a private-only architecture that must be rewritten for publication.
- Keep ChatGPT as a client; durable task/session/auth/policy state belongs server-side.
- Keep Hermes and Nous behind adapter boundaries rather than coupling the product to internal file/class layout.
- Verify actual upstream/runtime capabilities before implementing against a plan assumption.
- Unsupported capabilities must fail explicitly; never fabricate working behavior.
- Never commit or expose passwords, OAuth codes/tokens, API keys, private keys, cookies, session tokens, or other secrets.
- Update `STATE.md` only with verified reality when project state changes.
- Add an ADR under `docs/decisions/` when a long-lived architecture decision changes.
- Use the roadmap-aware issue/PR fields to record milestone, surface, acceptance criteria, temporary debt, and production replacement path.

## Current critical path

The current milestone is **M1 — Hermes Remote Control**. Before building further ChatGPT product UX, verify the real Hermes remote-control/session interface and implement the shared runtime/control-plane foundation described by `PROJECT.md`, `STATE.md`, and `ARCHITECTURE.md`.

## Existing Hermes instructions still apply

For Hermes codebase mechanics, testing, profiles, tool registration, prompt caching, and other upstream development rules, follow the existing root `AGENTS.md`.
