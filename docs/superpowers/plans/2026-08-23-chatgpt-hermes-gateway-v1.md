# ChatGPT ↔ Hermes Gateway V1 Implementation Plan

**Date:** 2026-08-23
**Design:** `docs/superpowers/specs/2026-08-23-chatgpt-hermes-app-design.md`
**Goal:** Ship the first BYO-Hermes control plane and ChatGPT plugin integration without changing the Hermes agent loop.

## Grounded implementation decisions

- Use Hermes' existing API-server runtime surface as the first runtime adapter. The current fork already exposes `/v1/runs` and `/v1/runs/{run_id}/events`, so the control plane should proxy/normalize those capabilities rather than instantiate `AIAgent` directly.
- Implement the ChatGPT-facing endpoint with the official MCP Python SDK, using its Streamable HTTP ASGI application. Keep MCP transport state stateless; persistent Hermes context is represented explicitly through `session_id`/run records rather than transport sessions.
- Use MCP's built-in OAuth 2.1 resource-server hooks (`TokenVerifier` + `AuthSettings`) when OAuth is configured, so protected-resource metadata and `WWW-Authenticate` challenges are protocol-compliant. Keep a development/private-tunnel auth mode for the first owner-only deployment.
- Keep the control plane as a standalone package under `apps/hermes-chatgpt-gateway/` so the managed-hosting worker can later be deployed separately.
- Store control-plane metadata in SQLite for self-hosted V1, behind a repository interface that can later be replaced by Postgres without changing services or tools.
- Do not store raw Hermes credentials in SQLite. Runtime credentials are supplied by environment-variable references in V1. A durable encrypted secrets backend is deferred to V1.1.
- Package a ChatGPT/Codex plugin scaffold under `plugins/hermes/`. The final `.app.json` mapping cannot be generated until ChatGPT registers the deployed MCP endpoint and returns its `plugin_asdk_app...` technical ID, so V1 includes the required manifest plus an `.app.json.example` template and exact registration instructions.

## Task 1 — Scaffold the standalone gateway and contract tests

**Files**
- Create `apps/hermes-chatgpt-gateway/pyproject.toml`
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/__init__.py`
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/models.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_models.py`

**TDD**
1. Write tests for run requests, autonomy enum validation, normalized results, and normalized error payloads.
2. Run: `pytest apps/hermes-chatgpt-gateway/tests/test_models.py -q`
3. Confirm RED because the package/models do not exist.
4. Implement the smallest Pydantic models required by the design.
5. Re-run the same command and confirm GREEN.

**Contract details**
- Autonomy: `plan | approve_actions | execute | continuous`.
- Agent profiles: predefined strings plus `custom:<id>`.
- Normalized statuses: `queued | running | awaiting_approval | completed | failed | cancelled`.
- Stable error codes: `HERMES_UNAVAILABLE`, `AWAITING_APPROVAL`, `POLICY_DENIED`, `PLAN_LIMIT_REACHED`, `AUTH_REQUIRED`, `INVALID_RUNTIME_CONFIG`, `RUNTIME_ERROR`.

## Task 2 — Tenant metadata repository and policy engine

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/database.py`
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/policy.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_database.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_policy.py`

**TDD**
1. Write repository tests that create a tenant, register a BYO runtime, look up a subject → tenant mapping, and persist run/session metadata.
2. Write policy tests showing requested autonomy/capabilities are capped server-side.
3. Run both test files and confirm RED.
4. Implement SQLite schema/repository and policy evaluation.
5. Re-run and confirm GREEN.

**V1 tables**
- `users`
- `tenants`
- `tenant_members`
- `hermes_connections`
- `agent_jobs`
- `agent_sessions`
- `usage_events`
- `audit_events`

`subscriptions`, `hermes_instances`, and durable `integration_credentials` remain schema-compatible follow-up work for managed V1.1 rather than active V1 behavior.

## Task 3 — Hermes runtime adapter

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/runtime.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_runtime.py`

**TDD**
1. Use `httpx.MockTransport` to model the existing Hermes API server.
2. Test capability/health checks.
3. Test `POST /v1/runs` → normalized `run_id`/status.
4. Test event-stream consumption and normalization.
5. Test unreachable runtime → `HERMES_UNAVAILABLE`.
6. Test auth/runtime misconfiguration without leaking bearer tokens.
7. Confirm RED, implement `RuntimeAdapter` + `ByoHermesAdapter`, confirm GREEN.

**Adapter boundary**
- `capabilities()`
- `start_run(request)`
- `get_run(run_id)`
- `get_result(run_id)`
- `approve(run_id, approval)`
- `stop_run(run_id)`
- `continue_session(session_id, instruction)`

Where the current Hermes API lacks a direct lifecycle endpoint, V1 derives state from the structured event stream or returns `INVALID_RUNTIME_CONFIG` rather than fabricating support.

## Task 4 — Run lifecycle service

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/service.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_service.py`

**TDD**
1. Test subject → tenant → connection resolution.
2. Test policy rejection before any runtime call.
3. Test run creation persists only metadata, never runtime credentials.
4. Test status/result/cancel/continue/approve route through the same adapter.
5. Test audit events for privileged actions.
6. Implement minimal service and confirm GREEN.

## Task 5 — OAuth/resource-server auth and private-tunnel development mode

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/auth.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_auth.py`

**TDD**
1. Test static development token verification maps a token to a subject and scopes without logging the token.
2. Test RFC 7662 introspection verifier with mocked HTTP responses.
3. Test inactive/missing-scope tokens reject.
4. Test auth configuration fails closed when production OAuth settings are incomplete.
5. Implement `TokenVerifier` integration for the MCP SDK.

**Modes**
- `private`: explicit static bearer token intended for Secure MCP Tunnel/private development only.
- `oauth_introspection`: production resource-server mode using an external OAuth 2.1 authorization server and token introspection.

No authorization-code/token issuer is implemented in this repository; the gateway is a resource server.

## Task 6 — Authenticated HTTP API

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/http_api.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_http_api.py`

**Endpoints**
- `GET /health`
- `POST /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/result`
- `POST /api/v1/runs/{run_id}/approve`
- `POST /api/v1/runs/{run_id}/cancel`
- `POST /api/v1/sessions/{session_id}/continue`

**TDD**
- Validate authentication, schema errors, tenant isolation, normalized errors, and no credential disclosure.

## Task 7 — MCP tools for ChatGPT

**Files**
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/mcp_server.py`
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/app.py`
- Create `apps/hermes-chatgpt-gateway/tests/test_mcp_tools.py`

**Tools**
- `hermes_run`
- `hermes_status`
- `hermes_result`
- `hermes_continue`
- `hermes_approve`
- `hermes_cancel`

**Tool behavior**
- Use focused input/output schemas.
- Return structured content plus concise model-readable text.
- Apply accurate read-only/destructive/open-world annotations.
- Resolve caller identity from the verified MCP access token; never accept tenant ID as a trusted tool argument.
- Keep tool handlers thin and delegate all authorization/routing to `HermesService`.

**TDD/validation**
- Unit test tool handlers against a fake service locally.
- In dependency-enabled CI, use the MCP SDK client/Inspector-compatible protocol to list and call tools over Streamable HTTP.

## Task 8 — Plugin package scaffold

**Files**
- Create `plugins/hermes/.codex-plugin/plugin.json`
- Create `plugins/hermes/.app.json.example`
- Create `plugins/hermes/README.md`
- Create `plugins/hermes/skills/use-hermes/SKILL.md`
- Create `.agents/plugins/marketplace.json` or merge a Hermes entry if the file already exists.

**Checks**
- Validate JSON.
- Manifest paths start with `./`.
- Do not invent a registered `plugin_asdk_app...` ID. Explain that `.app.json` is generated/filled only after ChatGPT developer-mode registration of the deployed `/mcp` endpoint.

## Task 9 — Deployment packaging and operator docs

**Files**
- Create `apps/hermes-chatgpt-gateway/Dockerfile`
- Create `apps/hermes-chatgpt-gateway/.env.example`
- Create `apps/hermes-chatgpt-gateway/README.md`
- Create `apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway/main.py`

**Document**
- Private owner-only deployment next to Hermes on Oracle VPS.
- Required Hermes API-server configuration (`API_SERVER_ENABLED`, host/port/key`) without including real credentials.
- Secure MCP Tunnel path for private ChatGPT developer-mode testing.
- Public HTTPS/OAuth requirements for eventual public plugin submission.
- BYO registration bootstrap command/API.

## Task 10 — CI and end-to-end test harness

**Files**
- Create `.github/workflows/hermes-chatgpt-gateway.yml`
- Create `apps/hermes-chatgpt-gateway/tests/test_e2e_fake_runtime.py`

**Validation commands**
- `python -m compileall apps/hermes-chatgpt-gateway/hermes_chatgpt_gateway`
- `pytest apps/hermes-chatgpt-gateway/tests -q`
- `python -m json.tool plugins/hermes/.codex-plugin/plugin.json`
- `python -m json.tool .agents/plugins/marketplace.json`
- CI installs project dependencies, then runs the full suite including MCP SDK transport tests.

The E2E harness starts a fake Hermes runtime, starts the gateway, invokes a multi-step run through the MCP tool service, checks status/result, verifies an approval-required response, exercises approve/continue/cancel, and asserts runtime credentials never appear in responses.

## Task 11 — Deployment/connection attempt

After code and CI are green:

1. Inspect available Vercel/hosting options for the control plane without changing the approved control-plane/runtime separation.
2. Prefer the Oracle VPS + Secure MCP Tunnel for the first private owner deployment if the necessary Oracle endpoint/credentials are not available in this session.
3. If a public gateway is deployed, verify `/mcp` over HTTPS and OAuth discovery before registering it in ChatGPT.
4. Register the MCP endpoint in ChatGPT developer mode only when a reachable endpoint exists; copy the returned technical `plugin_asdk_app...` ID into a real `plugins/hermes/.app.json` in a follow-up commit.
5. Do not invent or hardcode the user's Oracle endpoint or secret.

## Task 12 — Review and completion gates

1. Run the primary validation suite.
2. Primary self-review against the approved design and acceptance criteria.
3. Run the required clean-room loop with fresh review context each pass:
   - Luna-equivalent low review until clean, max 12.
   - Terra-equivalent medium review until clean, max 8.
   - Sol-equivalent high review until clean, max 5.
4. Because this ChatGPT session does not expose separate reviewer model instances, each stage must be reported as the closest supported fresh-context independent review by the same GPT-5.6 Sol model; do not claim true tier/model isolation.
5. Apply valid findings and rerun validation plus the same review stage before advancing.
6. Run verification-before-completion.
7. Open a PR from `feature/chatgpt-hermes-gateway-v1` to `main` with validation evidence and explicit remaining deployment blockers.

## V1 completion definition

V1 code is complete when all locally/CI-testable acceptance criteria pass. Live Oracle/ChatGPT E2E is complete only if this session has a reachable Oracle Hermes endpoint plus permission to register/test the MCP connection. If those are unavailable, report that exact live-integration portion as unverified rather than treating it as passed.
