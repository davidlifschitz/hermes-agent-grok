# M1 Verified Hermes Runtime Adapter Plan

**Roadmap milestone:** M1 — Hermes Remote Control  
**Surface:** Shared Core  
**Status:** implemented protocol proof; M1 gate remains incomplete

## Verified runtime surface

The older plan named non-existent `hermes_cli/api_server.py` and
`hermes_cli/api_app.py`. The current fork instead implements the remotely
controllable runtime as `gateway.platforms.api_server.APIServerAdapter`, started
by the messaging gateway:

```bash
API_SERVER_ENABLED=true API_SERVER_KEY=<server-side-secret> hermes gateway run
```

There is no top-level `hermes serve`. `hermes mcp serve` is a stdio MCP bridge
for messaging conversations, not the generic agent-run HTTP service.

### Capability matrix

| Capability | Finding | Evidence-backed interface |
|---|---|---|
| Health | VERIFIED PRESENT | `GET /health`, `GET /v1/health` |
| Submit asynchronous work | VERIFIED PRESENT | `POST /v1/runs` -> `202 {run_id,status}` |
| Progress and terminal result | VERIFIED PRESENT | one-shot `GET /v1/runs/{run_id}/events` SSE |
| Chat/Responses submission | VERIFIED PRESENT | `POST /v1/chat/completions`, `POST /v1/responses` |
| Responses retrieval/chaining | VERIFIED PRESENT | response GET/DELETE and `previous_response_id` |
| Durable async run status/result | VERIFIED ABSENT | no run GET/result route; SSE queue is in memory |
| Run replay/reconnect | VERIFIED ABSENT | one consumptive queue; removed after streaming; 300s orphan TTL |
| HTTP run cancellation | VERIFIED ABSENT | no run cancellation route |
| HTTP approvals | VERIFIED ABSENT | no approval route or response protocol |
| Run continuation | PARTIAL | IDs are accepted, but `/v1/runs` does not prove history reuse |
| Network WebSocket/JSON-RPC | VERIFIED ABSENT | ACP JSON-RPC is local stdio; vendor WebSockets are platform-specific |
| HTTP authentication | PARTIAL | optional static bearer key; no OAuth, tenancy, or scopes |
| ACP cancel/permissions | VERIFIED PRESENT | local editor-client stdio only |
| Portal OAuth/inference | VERIFIED PRESENT in source/tests | device flow, refresh, agent-key mint |
| Portal MCP endpoint | UNVERIFIED | generic MCP OAuth exists; no checked-in endpoint-specific adapter |
| Hermes Cloud discovery/lifecycle | VERIFIED ABSENT | no discovery/create/start/stop adapter in this checkout |

## Corrected shared contract

The first adapter wraps only the verified HTTP DTOs. It probes reachability,
starts a run, and consumes its event stream through the terminal result.
Capabilities are declared explicitly. Durable lookup, continuation,
cancellation, and approvals raise `UNSUPPORTED_CAPABILITY`.

Product `task_id` and tenant-scoped session state must be separate from Hermes
`run_id`/`session_id`. A later control-plane `TaskService` must own the sole SSE
consumer and persist normalized events/results so clients can reconnect. The
adapter must never import `AIAgent`, gateway configuration, SessionDB, or Portal
types.

## Acceptance criteria and evidence

- Adapter health -> submit -> observe -> terminal result is exercised against
  both a local aiohttp wire fixture and the real `APIServerAdapter` handlers;
  only the external LLM execution boundary is stubbed.
- Unsupported lifecycle operations produce typed capability errors.
- Existing API server, Portal OAuth/MCP, and managed-tool tests remain green.
- A real provider-backed Hermes task is **unverified** because it requires an
  external inference account/credential and would incur an authenticated call.

## Temporary debt and production replacement path

The adapter's event stream is non-replayable and the runtime hop uses a static
key. M2 must introduce a durable tenant-scoped TaskService/repository that
consumes SSE independently of ChatGPT. Before remote exposure, require the
runtime-hop secret plus TLS/private ingress and fail-closed tool policy. Add or
verify upstream durable status/result, cancellation, continuation, approvals,
and capability negotiation before advertising those operations.

Nous Portal/Hermes Cloud lifecycle remains a separate adapter boundary. Live
Portal MCP tool enumeration requires the owner to authorize in a personal
browser on the official page; no code or token should be pasted into chat.

## Exact next step toward M2

Implement a tenant-scoped TaskService and persistence interface that creates a
product task ID, starts this runtime adapter, consumes/persists events in a
server-owned worker, and serves status/result from stored product state.
