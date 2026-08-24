## Roadmap alignment

- **Milestone:** M0 / M1 / M2 / M3 / M4 / M5 / M6
- **Surface:** shared / private / public / upstream Hermes
- **Capability advanced:**
- **Blocks/unblocks:**

## End-state compatibility

- **Does this use the shared control-plane/runtime boundaries?** Yes / No / N/A
- **Does this create a private-only implementation that must be rewritten for publication?** Yes / No
- **Temporary infrastructure or debt:**
- **Production replacement/removal path:**

## What changed

Describe the behavior and files changed.

## Acceptance criteria

- [ ] Relevant roadmap gate/acceptance behavior is identified.
- [ ] Unsupported upstream capabilities fail explicitly rather than being fabricated.
- [ ] Credentials/secrets are not committed, logged, or returned to model context.
- [ ] Tenant/auth boundaries are preserved where applicable.
- [ ] Relevant tests/validation pass.
- [ ] End-to-end behavior was verified when the change affects an E2E path, or the unverified portion is explicitly documented.
- [ ] `STATE.md` was updated if verified project reality changed.
- [ ] An ADR was added if this changes a long-lived architecture decision.

## Validation

Commands/tests/manual E2E exercised:

```text
<validation evidence>
```

## Remaining risks / blockers

List anything that remains unverified, mocked, account-dependent, or dependent on external infrastructure.
