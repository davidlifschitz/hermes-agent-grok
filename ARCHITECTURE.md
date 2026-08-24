# Hermes for ChatGPT — Architecture

This document contains the long-lived architecture constraints for the ChatGPT ↔ Hermes product.

For current implementation reality, see [`STATE.md`](STATE.md). For sequencing, see [`ROADMAP.md`](ROADMAP.md).

## Architectural objective

Provide a stable, cloud-hosted control plane that lets ChatGPT delegate work to Hermes without coupling the ChatGPT product to Hermes internals, a specific hosting provider, or a private developer-only deployment path.

## System shape

```text
ChatGPT clients
(web / mobile / desktop / Codex)
              |
              | MCP / HTTPS
              v
      Hermes Control Plane
      ┌───────────────────────────────┐
      │ authentication / tenants      │
      │ agent/runtime registry        │
      │ task router                   │
      │ session manager               │
      │ policy / approvals            │
      │ persistence                   │
      │ audit / usage                 │
      │ reliability / observability   │
      └──────────┬───────────┬────────┘
                 │           │
                 │           │
                 v           v
         Nous Portal MCP   Hermes runtime
         lifecycle/fleet   execution/session/events
```

Cloudflare may provide DNS, TLS, secure ingress, tunneling, WAF, and rate limiting around the control plane. It is not the control plane itself.

## Core boundaries

### ChatGPT client boundary

ChatGPT should receive only the tool contracts and user-visible state needed to operate the product.

ChatGPT must not own:

- Hermes credentials,
- Nous refresh/access tokens,
- long-running task state,
- session persistence,
- runtime routing,
- tenant authorization,
- infrastructure secrets.

### Control-plane boundary

The control plane owns durable product state and authorization.

It should expose domain operations such as:

```text
agents.list
agents.get
agents.create
agents.start
agents.stop
agents.restart
agents.destroy

sessions.list
sessions.get
sessions.create

tasks.start
tasks.get
tasks.result
tasks.continue
tasks.cancel

approvals.list
approvals.respond
```

The initial ChatGPT-facing MCP surface may intentionally expose a smaller subset.

### Runtime adapter boundary

Hermes is accessed through a stable runtime interface rather than direct imports from the agent loop.

Target capability shape:

```text
capabilities()
start_run(request)
get_run(run_id)
get_result(run_id)
continue_session(session_id, instruction)
approve(run_id, approval)
stop_run(run_id)
```

Exact transport/protocol details must be grounded in verified Hermes runtime capabilities. Unsupported capabilities return explicit errors.

### Nous Portal boundary

Nous Portal/Hermes Cloud lifecycle management is an integration behind an adapter.

Responsibilities may include:

- account/org-aware agent discovery,
- lifecycle operations,
- status/cost metadata,
- hosted model/tool access where supported.

Do not couple the entire product data model to undocumented Portal internals.

## Long-running task model

Agent work is represented by durable server-side task/run state.

A task submission should be able to return quickly with a stable identifier:

```json
{
  "task_id": "tsk_...",
  "state": "running"
}
```

Clients then inspect, continue, approve, or cancel that task through explicit operations.

Do not require a single ChatGPT tool invocation or HTTP connection to remain open for the full duration of an arbitrary Hermes task.

## Identity and tenancy

All production-owned state is tenant scoped.

Typical ownership chain:

```text
user
→ tenant / Nous organization
→ runtime connection / agent
→ session
→ task
→ approvals / audit / usage
```

Tenant identity is derived from verified authentication, never from an untrusted MCP tool argument.

## Secrets boundary

Secrets and credentials are stored and used server-side.

Never:

- commit credentials,
- put tokens in prompts,
- return tokens in tool results,
- trust a client-provided tenant ID as authorization,
- log raw bearer/refresh tokens.

Private development may use simpler authentication, but it must be isolated behind the same service boundary so production auth can replace it without rewriting task/runtime logic.

## Private/public convergence

Private and public delivery paths are deployment/configuration channels, not separate products.

By M4 they must share:

```text
runtime adapters
lifecycle adapters
task/session engine
persistence contracts
policy/approval logic
auth/tenant domain model
audit/usage model
MCP/domain tool schemas
tests
```

Allowed differences include client IDs, domains, environment configuration, feature exposure, rate limits, and canary flags.

## Function-agnostic product model

The control plane should not assume that an agent is a coding agent.

Agent profiles may represent developer, researcher, marketer, sales, operations, SEO, productivity, or custom work. The shared task/session contract should remain generic enough to support those categories without creating separate control planes.

## Replaceability

The product should be able to support additional agent harnesses later by implementing the runtime adapter contract.

This does not mean we should build a multi-harness abstraction prematurely. It means new ChatGPT-facing code must not depend unnecessarily on Hermes internal classes or file layout.

## Error model

Prefer stable normalized error classes over leaking upstream errors directly.

Examples:

- `HERMES_UNAVAILABLE`
- `AUTH_REQUIRED`
- `AWAITING_APPROVAL`
- `POLICY_DENIED`
- `PLAN_LIMIT_REACHED`
- `INVALID_RUNTIME_CONFIG`
- `RUNTIME_ERROR`

Do not report a capability as working when the upstream runtime cannot support it.

## Reliability expectations

Before release candidate, the shared control plane should support the relevant combination of:

- idempotency,
- task queues,
- retries,
- runtime health checks,
- reconnect/recovery,
- timeouts,
- cancellation,
- checkpoints where supported,
- audit trails,
- observability.

## Source-of-truth hierarchy

When project artifacts disagree, resolve them in this order:

1. Verified code/runtime behavior.
2. `STATE.md`.
3. Accepted ADRs in `docs/decisions/` and this architecture document.
4. `ROADMAP.md` / `PROJECT.md`.
5. Detailed implementation specs and plans.
6. Conversation history or memory.
