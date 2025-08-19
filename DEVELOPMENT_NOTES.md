# Developer Notes: Messaging Adapters and Tests

This document tracks design decisions and testing strategy as the messaging service evolves.

## Adapter Abstraction

- Introduced `app.adapters.base.MessagingAdapter` protocol to standardize provider interfaces.
- Implemented `LoopClient` to conform to the protocol and added helpers:
  - `verify_request(authorization_header)` to enforce inbound webhook auth via env `LOOP_WEBHOOK_AUTH`.
  - `normalize_event(body)` to map inbound payloads into a common shape.
- Added `AdapterRegistry` for pluggable provider lookup. New providers (e.g., Twilio, WhatsApp) should implement the protocol and register with a unique key.

## Router Wiring

- `app.routers.loop_webhook` now resolves the adapter from the registry and uses `normalize_event` and `send_text` to keep provider-specific logic out of the router.
- LLM calls are funneled through `app.agents.dspy_agent.generate_reply`, which tests stub via a context manager.

## Tests

- Tests use FastAPI `TestClient` and `respx` to mock outbound HTTP.
- LLM is stubbed to deterministic strings.
- Covered: adapter send payloads, normalization, registry behavior, webhook happy/error paths, health and root routes.

## Next Steps

- Add alternative adapters (Twilio/WhatsApp) and expand normalization accordingly.
- Implement signature verification if providers expose HMACs.
- Add persistence-backed idempotency for webhook processing.
- Introduce structured logging and metrics.
