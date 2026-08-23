# ChatGPT ↔ Hermes App Design

Date: 2026-08-23
Status: Proposed for implementation

## 1. Goal

Build a ChatGPT app/plugin that lets a user invoke Hermes Agent from ChatGPT through a stable MCP/API gateway. The system must support both:

1. **BYO Hermes** — users connect a Hermes instance they operate themselves.
2. **Managed Hermes** — paid users receive an isolated Hermes runtime operated by the platform.

The first tenant is the project owner using an existing Oracle VPS-hosted Hermes instance. The design must remain usable if the ChatGPT account cannot yet exercise every custom MCP write action natively; therefore the gateway will expose both MCP and authenticated HTTP APIs.

## 2. Product model

### Free / self-hosted

- Connect one user-operated Hermes instance.
- Core run lifecycle tools.
- User pays their own compute and model/provider costs.
- User is responsible for Hermes uptime and runtime maintenance.

### Paid / managed

- One isolated Hermes runtime per tenant.
- Persistent storage and memory.
- Managed updates, health checks, restart behavior, backups, and secrets.
- Scheduled agents and higher concurrency.
- Platform-enforced quotas and plan limits.

The ChatGPT-facing interface is identical for BYO and managed tenants so users can upgrade without changing workflows.

## 3. High-level architecture

```text
ChatGPT
  ↓ OAuth + MCP
Hermes Control Plane / MCP Gateway
  ├─ authentication
  ├─ tenant resolution
  ├─ authorization / policy checks
  ├─ billing / entitlement checks
  ├─ job metadata
  └─ runtime routing
       ↓
       ├─ BYO Hermes endpoint
       └─ Managed tenant Hermes runtime
```

The control plane never exposes SSH keys, Oracle credentials, provider API keys, or Hermes secrets to ChatGPT.

## 4. Control plane responsibilities

The control plane is responsible for:

- ChatGPT-compatible OAuth.
- MCP tool exposure.
- Normal HTTP API exposure for non-ChatGPT clients.
- User and tenant records.
- Tenant membership and role resolution.
- BYO Hermes connection profiles.
- Managed runtime provisioning metadata.
- Subscription state and plan entitlements.
- Per-tenant permissions.
- Job/session metadata and audit logging.
- Runtime health metadata.
- Usage accounting.

The control plane does **not** execute agent work directly.

## 5. Runtime plane responsibilities

Hermes remains the orchestration and execution engine.

Each managed tenant receives:

- one isolated Hermes container/runtime,
- one persistent volume,
- one secrets namespace,
- resource limits,
- concurrency limits,
- outbound network policy,
- health checks,
- restart behavior,
- version pinning.

A runtime crash or runaway task must not affect the control plane or another tenant.

Initial managed infrastructure should use Docker on one or more VPS hosts. Kubernetes, Nomad, ECS, or another orchestrator is deferred until tenant count or operational complexity justifies it.

## 6. Tenant connection modes

### BYO_HERMES

Stored configuration:

```text
connection_type = byo
runtime_owner = user
endpoint = <encrypted connection profile>
```

The control plane proxies approved requests to the user's Hermes instance.

### MANAGED_HERMES

Stored configuration:

```text
connection_type = managed
runtime_owner = platform
instance_id = <managed runtime id>
```

The control plane routes requests to the tenant's isolated managed runtime.

## 7. ChatGPT-facing tool contract

Version 1 exposes a deliberately small surface:

- `hermes.run`
- `hermes.status`
- `hermes.continue`
- `hermes.result`
- `hermes.approve`
- `hermes.cancel`

Version 1.1 adds:

- `hermes.schedule`

The intent is to let Hermes perform internal delegation rather than exposing each Hermes subagent as a separate MCP tool.

### hermes.run

Primary request fields:

```json
{
  "goal": "string",
  "relevant_context": "string or structured content",
  "constraints": ["string"],
  "completion_criteria": ["string"],
  "agent_profile": "general | researcher | developer | marketer | sales | operations | custom:<id>",
  "autonomy": "plan | approve_actions | execute | continuous",
  "requested_capabilities": ["string"],
  "session_id": "optional string"
}
```

The gateway resolves tenant identity and policy server-side. ChatGPT may request capabilities, but the request never overrides tenant permissions.

### hermes.status

Returns normalized state for a Hermes run.

### hermes.continue

Adds a new instruction to an existing Hermes session/run context without requiring ChatGPT to resend the full prior conversation.

### hermes.result

Returns normalized final output and artifacts.

### hermes.approve

Approves or denies a specific pending runtime action. Approval remains subject to tenant policy; the tool cannot authorize an action that server-side policy forbids.

### hermes.cancel

Stops an active run when supported by the runtime.

## 8. Autonomy model

Each run declares one of four requested autonomy levels:

- `plan` — investigate and propose; no external side effects.
- `approve_actions` — prepare actions, but externally consequential actions require approval.
- `execute` — perform all actions permitted by tenant policy.
- `continuous` — request a persistent objective. In V1 this may only remain active within Hermes' supported run/session lifecycle; scheduled/repeated execution is not exposed through the gateway until `hermes.schedule` ships in V1.1.

Requested autonomy is capped by server-side tenant policy.

## 9. Permission model

Permissions are configured per tenant and enforced by the gateway/runtime boundary.

Example:

```text
GitHub:
  read: yes
  write: yes

Shell:
  read_files: yes
  execute: yes

X:
  read: yes
  post: approval_required

Reddit:
  read: yes
  post: approval_required

Email:
  read: yes
  send: never

Payments:
  none
```

The gateway must reject disallowed actions even if ChatGPT requests `autonomy = execute`.

## 10. Authentication and identity

Keep these identities separate:

1. **ChatGPT identity** — authenticates the user to the app.
2. **Tenant identity** — determines runtime, sessions, permissions, and billing ownership.
3. **External integration identities** — GitHub/social/provider credentials owned by the tenant.

OAuth tokens and runtime credentials are stored server-side and encrypted at rest.

The OAuth implementation must support refresh-token style long-lived sessions where supported by the ChatGPT app flow.

## 11. Initial data model

Initial tables/entities:

```text
users
tenants
tenant_members
hermes_connections
hermes_instances
agent_jobs
agent_sessions
integration_credentials
subscriptions
usage_events
```

Additional tables may be introduced only when required by implementation.

## 12. Request routing

```text
incoming request
  ↓
authenticate ChatGPT / API caller
  ↓
resolve user + tenant
  ↓
load subscription + entitlement state
  ↓
load policy
  ↓
validate requested autonomy/capabilities
  ↓
resolve runtime
  ├─ BYO → user's Hermes endpoint
  └─ managed → platform runtime endpoint
  ↓
execute Hermes request
  ↓
normalize status/result
  ↓
persist metadata + usage
  ↓
return structured response
```

## 13. Hermes integration strategy

Prefer wrapping Hermes' existing programmatic API rather than changing the Hermes agent loop.

Where the runtime supports it, map gateway operations to Hermes run lifecycle endpoints such as:

```text
POST /v1/runs
GET  /v1/runs/{id}
GET  /v1/runs/{id}/events
POST /v1/runs/{id}/approval
POST /v1/runs/{id}/stop
GET  /v1/capabilities
```

If the installed Hermes version differs, introduce an adapter layer rather than coupling the control plane directly to version-specific endpoint details.

## 14. Runtime adapter boundary

Define an internal interface conceptually equivalent to:

```text
RuntimeAdapter
  capabilities()
  startRun(request)
  getRun(runId)
  streamEvents(runId)
  approve(runId, approval)
  stopRun(runId)
  continueSession(sessionId, instruction)
```

Implementations:

- `ByoHermesAdapter`
- `ManagedHermesAdapter`

Both must return the same normalized internal result types.

## 15. Normalized response contract

Successful final result:

```json
{
  "status": "completed",
  "summary": "string",
  "actions": [],
  "artifacts": [],
  "links": [],
  "warnings": [],
  "usage": {},
  "session_id": "string",
  "run_id": "string"
}
```

Error categories:

```text
HERMES_UNAVAILABLE
AWAITING_APPROVAL
POLICY_DENIED
PLAN_LIMIT_REACHED
AUTH_REQUIRED
INVALID_RUNTIME_CONFIG
RUNTIME_ERROR
```

Errors should include machine-readable codes plus user-facing details suitable for ChatGPT.

## 16. Failure behavior

### BYO runtime offline

Return `HERMES_UNAVAILABLE` with retryability and last-known health metadata where available.

### Approval required

Return `AWAITING_APPROVAL` with run id, requested action, and risk metadata. The caller may respond through `hermes.approve` if tenant policy allows approval of that action.

### Policy violation

Return `POLICY_DENIED` with the requested capability and blocking policy.

### Managed quota exceeded

Return `PLAN_LIMIT_REACHED` with current usage and limit metadata.

### Runtime version mismatch

Adapter layer returns `INVALID_RUNTIME_CONFIG` or `RUNTIME_ERROR`; the control plane must not leak secrets or internal stack traces.

## 17. Onboarding

```text
Install ChatGPT app
  ↓
Sign in to Hermes control plane
  ↓
Choose connection mode

A. Connect my Hermes
   → provide endpoint / credential
   → prove ownership
   → capability scan
   → save encrypted connection profile

B. Managed Hermes
   → choose paid plan
   → subscription checkout
   → provision isolated runtime
   → configure provider/model
   → capability scan

  ↓
ChatGPT tool access becomes available
```

## 18. Security principles

- Never expose runtime credentials to ChatGPT.
- Never trust a capability request from the client without policy validation.
- Isolate managed tenants at runtime and secrets levels.
- Keep control plane and runtime plane separate.
- Record privileged actions in an audit trail.
- Use least-privilege credentials for runtime integrations.
- Do not expose arbitrary shell execution as a first-class ChatGPT MCP tool.
- Treat Hermes as the execution boundary for shell/tool orchestration.
- Redact secrets from logs and returned events.

## 19. MVP scope

Version 1 includes:

1. MCP server compatible with ChatGPT app tooling.
2. Authenticated HTTP API exposing the same logical operations.
3. OAuth/authentication layer.
4. Tenant database.
5. BYO Hermes registration.
6. First Oracle VPS-backed tenant connection.
7. `run`, `status`, `result`, `continue`, `approve`, `cancel`.
8. Server-side permission policies.
9. Basic runtime health checks.
10. Basic web dashboard for connected runtimes and run history.
11. Audit metadata.
12. Managed-runtime-compatible schema and adapter interfaces, without paid provisioning in V1.

Explicitly deferred from V1:

- Stripe or other billing integration.
- automatic managed runtime provisioning.
- multi-host scheduler.
- public marketplace.
- team collaboration UI beyond minimal tenant membership support.
- advanced usage billing.
- scheduled Hermes jobs.

## 20. V1.1 scope

- paid subscription/paywall,
- managed Docker provisioning,
- per-tenant secrets management,
- quotas,
- health/restart automation,
- backups,
- `hermes.schedule`,
- onboarding wizard,
- managed runtime model/provider setup.

## 21. V2 scope

- public ChatGPT app distribution,
- team workspaces,
- multiple Hermes runtimes per tenant,
- reusable agent profiles,
- profile sharing/marketplace,
- richer ChatGPT UI components,
- usage-based managed tiers,
- runtime placement across multiple workers.

## 22. Testing strategy

Test four layers independently:

1. **MCP contract tests** — tool schema, auth failures, structured errors.
2. **Control-plane tests** — tenant routing, permissions, entitlement checks, normalization.
3. **Runtime adapter tests** — Hermes API mapping, timeouts, approvals, retries.
4. **End-to-end tests** — real isolated Hermes runtime.

Primary V1 acceptance test:

> From ChatGPT, a user can ask Hermes to perform a multi-step job. Hermes can delegate/use tools. ChatGPT can inspect status, receive an approval-required response, approve or deny the pending action through `hermes.approve`, continue the run, cancel an active run, and retrieve a final structured result without receiving Hermes server credentials.

## 23. Deployment strategy

Initial deployment should minimize moving parts:

- control plane on a conventional app hosting platform,
- relational database for tenants/jobs/subscriptions metadata,
- secrets stored through the hosting platform or dedicated secret storage,
- user's Oracle VPS as the first BYO Hermes runtime,
- managed runtime worker introduced in V1.1.

The control plane and managed runtime plane must use separate deployment units.

## 24. Repository structure

For the first implementation, keep the gateway alongside this Hermes fork while preserving clean package boundaries:

```text
apps/
  hermes-chatgpt-gateway/
    src/
      auth/
      mcp/
      api/
      tenants/
      policy/
      runtime/
      jobs/
      usage/
    tests/

docs/
  superpowers/specs/
```

If the gateway becomes independently distributed, it may later move to a dedicated repository without changing the runtime adapter contract.

## 25. Non-goals

V1 does not attempt to:

- replace Hermes' internal subagent/delegation system,
- expose every Hermes tool individually through MCP,
- allow ChatGPT to bypass tenant policy,
- create a general-purpose remote shell plugin,
- provide fully managed Hermes hosting before the BYO path works end to end.

## 26. Implementation order

1. Define normalized request/result/error types.
2. Build runtime adapter abstraction.
3. Implement BYO Hermes adapter.
4. Build tenant/auth/policy layer.
5. Build run lifecycle service.
6. Expose authenticated HTTP API.
7. Expose MCP tools over the same services.
8. Register the owner's Oracle Hermes instance.
9. Add dashboard and health status.
10. Run E2E validation against the real Hermes runtime.
11. Only after V1 works, add paid managed-runtime provisioning.

## 27. Success criteria

V1 is successful when:

- ChatGPT can invoke Hermes through MCP using authenticated tenant context.
- The same functionality is accessible through the HTTP API.
- BYO routing works against the owner's Oracle-hosted Hermes instance.
- Credentials never appear in ChatGPT-visible payloads.
- Policy enforcement blocks disallowed actions server-side.
- Run state, approval state, approval/denial, cancellation, continuation, and final results are normalized.
- A real multi-step Hermes job passes the end-to-end acceptance test.
- Architecture supports later managed tenant runtimes without changing the ChatGPT tool contract.
