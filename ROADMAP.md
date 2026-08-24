# Hermes for ChatGPT — Roadmap

This roadmap governs development toward one full product with two delivery channels: private/canary and published/stable.

Do not advance a later milestone while an earlier milestone's core acceptance criteria remain mocked or unverified.

## M0 — Architecture and Contract

**Goal:** define the product boundary and stable shared contracts.

### Required outcomes

- Shared control-plane architecture documented.
- Private and publish pathways explicitly share one backend.
- Initial task/session/runtime contracts defined.
- Security boundaries documented.
- Existing detailed design/specs linked from the canonical docs.

### Gate

Architecture is coherent enough that implementation can proceed without inventing a second control plane.

**Status:** substantially complete; continue refining only when implementation evidence requires it.

---

## M1 — Hermes Remote Control

**Goal:** control a real Hermes runtime programmatically through a stable adapter.

### Required outcomes

- Verify the actual supported Hermes remote-control/session protocol.
- Implement a Hermes runtime adapter.
- Implement/verify Nous Portal lifecycle integration where applicable.
- Resolve a runtime/agent, start or reuse it, submit work, observe state/result, and stop/reuse it.
- Explicit errors for unsupported capabilities.

### Gate

A non-interactive client can complete:

```text
resolve Hermes
→ ensure running
→ submit task
→ receive result/state
→ stop or reuse runtime
```

**Status:** current milestone; not complete.

---

## M2 — Private ChatGPT Control

**Goal:** ChatGPT can drive the shared control plane end-to-end.

### Initial tool surface

- `hermes_run`
- `hermes_status`
- `hermes_result`
- `hermes_continue`
- `hermes_approve`
- `hermes_cancel`

Lifecycle/agent-management tools may be added behind the same service boundary as verified capabilities become available.

### Required outcomes

- MCP/HTTPS surface backed by the shared service.
- Server-side `task_id`/run state for long-running work.
- Session continuation and cancellation semantics.
- Owner-only private authentication mode.
- Private ingress/deployment suitable for dogfooding.
- Real ChatGPT-style tool-call E2E validation where account/product capabilities permit it.

### Gate

```text
ChatGPT/client
→ MCP
→ control plane
→ Hermes
→ result/status
→ ChatGPT/client
```

works without putting Hermes credentials in model context.

---

## M3 — Production Identity and Isolation

**Goal:** replace owner-only assumptions with production-shaped user and tenant boundaries.

### Required outcomes

- User identity and tenant/org resolution.
- Production OAuth/resource-server flow.
- Encrypted/durable secrets handling.
- Tenant-scoped runtimes, sessions, tasks, audit data, and usage data.
- Authorization/policy layer.
- Cross-tenant isolation tests.

### Gate

Two test identities cannot access or influence each other's Hermes resources, sessions, credentials, or tasks.

---

## M4 — Private/Public Convergence

**Goal:** merge the private and publication pathways into one product backend.

This is the critical architecture milestone.

### Required outcomes

Both channels use the same:

- Hermes runtime adapter,
- Nous lifecycle adapter,
- task/session engine,
- auth/tenant model,
- policy and approval layer,
- persistence model,
- audit/usage model,
- MCP/domain contracts,
- automated test suite.

The private pathway becomes staging/canary/admin. The publish pathway becomes stable production distribution.

### Gate

There is no separate private business-logic implementation to rewrite for publication.

---

## M5 — Release Candidate

**Goal:** make the shared product understandable, secure, observable, and reliable enough for external users.

### Required outcomes

- First-run connection/onboarding UX.
- Clear agent/task status and error handling.
- Destructive-action confirmation/approval semantics.
- Retry, idempotency, reconnect, timeout, and failure recovery.
- Audit and observability sufficient to diagnose failures without leaking secrets.
- Rate limits/quotas and cost controls where relevant.
- Security review and negative tests.
- Privacy/retention/support/release documentation.

### Gate

A user unfamiliar with Hermes can connect, delegate a task, inspect progress/result, continue it, and safely cancel/stop resources without understanding the underlying infrastructure.

---

## M6 — Published Product

**Goal:** ship the stable ChatGPT product through the supported publication/distribution path.

### Required outcomes

- Public HTTPS deployment.
- Production OAuth and domain configuration.
- Apps SDK/plugin packaging complete.
- Submission metadata, privacy policy, support information, assets, and test cases complete.
- Submission/review blockers resolved.

### Gate

The product is installable/usable through the supported ChatGPT distribution surface and invokes the same backend proven by the private canary channel.

---

## After M6

Potential extensions only after the core product is stable:

- scheduled/recurring Hermes objectives,
- multi-agent swarms,
- agent templates/profiles,
- GitHub/browser/marketing/SEO/sales workflows,
- shared team agents,
- artifact return,
- notifications,
- budgets and cost policies,
- additional agent harness adapters behind the same runtime contract.

These must not compromise the function-agnostic shared-control-plane model.
