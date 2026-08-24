# Private Path — Dogfood / Canary

## Purpose

Get a real owner-only Hermes ↔ ChatGPT workflow working early while exercising the same shared control-plane code intended for the public product.

## Allowed temporary simplifications

Examples may include:

- owner-only/static development authentication,
- private tunnel/domain configuration,
- single-tenant bootstrap configuration,
- SQLite or other lightweight persistence behind a repository interface,
- manually configured runtime connection details.

## Not allowed as shortcuts

Do not create private-only versions of:

- task/session business logic,
- Hermes runtime semantics,
- MCP/domain tool behavior,
- authorization/policy decisions,
- audit/usage concepts,
- core persistence contracts.

Those belong in the shared control plane.

## Success path

```text
ChatGPT/private client
→ MCP/HTTPS
→ shared control plane
→ Hermes runtime
→ task status/result
→ continue/approve/cancel as supported
```

## Long-term role

After M4, this pathway becomes the canary/staging/admin channel for features before they reach the published stable product.
