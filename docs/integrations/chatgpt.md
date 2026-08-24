# ChatGPT Integration

## Role

ChatGPT is the user-facing client/orchestration surface for the Hermes product, not the durable runtime/control plane.

The product should be usable from supported ChatGPT surfaces without requiring users to understand MCP, Cloudflare, VPS infrastructure, or Hermes internals.

## ChatGPT-facing contract

Initial focused MCP/domain operations:

```text
hermes_run
hermes_status
hermes_result
hermes_continue
hermes_approve
hermes_cancel
```

Agent lifecycle tools can be exposed as the underlying lifecycle capabilities are verified and policy semantics are defined.

## Client rules

- Tool handlers stay thin.
- Caller identity comes from verified authentication, not a trusted `tenant_id` argument.
- Long-running work returns durable server-side task/run identifiers.
- Secrets never appear in prompts or tool results.
- Destructive/open-world actions use accurate annotations and approval semantics.

## Private vs published access

Private access is the dogfood/canary channel. Published access is the stable distribution channel. They must converge on the same backend by M4.

## Current state

The repo contains product design/planning but the ChatGPT-facing gateway/plugin implementation is not yet verified as present on `main`. See [`STATE.md`](../../STATE.md).
