# Implementation Plans

This directory is the stable index for implementation planning related to the Hermes ↔ ChatGPT product.

Detailed historical/current design work already exists under `docs/superpowers/` and should not be duplicated merely to fit this directory structure.

## Current relevant artifacts

- Product design:
  - `docs/superpowers/specs/2026-08-23-chatgpt-hermes-app-design.md`
- V1 gateway implementation plan:
  - `docs/superpowers/plans/2026-08-23-chatgpt-hermes-gateway-v1.md` on `feature/chatgpt-hermes-gateway-v1`

## Rule

Implementation plans are proposals until verified by code/runtime evidence. If a plan conflicts with `STATE.md` or observed runtime behavior, update/rewrite the plan before implementing the conflicting assumption.

Every new implementation plan should identify:

- roadmap milestone,
- shared/private/public surface,
- dependencies,
- acceptance criteria,
- temporary infrastructure/debt,
- production replacement path,
- validation strategy.
