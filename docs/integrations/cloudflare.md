# Cloudflare Integration

## Role

Cloudflare is edge/transport infrastructure around the Hermes Control Plane.

Appropriate responsibilities include:

- DNS,
- TLS,
- outbound-origin tunneling/private origin access,
- WebSocket-capable ingress where needed,
- WAF/rate limiting,
- edge security controls.

## Non-responsibilities

Cloudflare is not responsible for:

- Hermes task orchestration,
- agent/session state,
- Nous account/org mapping,
- product tenant authorization,
- approvals,
- product billing/entitlements.

## Private pathway

A tunnel may expose only the product gateway/control-plane endpoint while keeping raw Hermes runtime endpoints private.

Example shape:

```text
ChatGPT/client
→ https://<gateway-domain>/mcp
→ Cloudflare
→ private control-plane origin
→ Hermes/Nous adapters
```

## Public pathway

The public product may retain Cloudflare for DNS/TLS/WAF/ingress, but application authentication remains a control-plane concern.

## Current state

Live tunnel/domain configuration is unverified in the canonical project state. See [`STATE.md`](../../STATE.md).
