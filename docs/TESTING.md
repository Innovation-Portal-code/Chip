# Testing Strategy

This repository includes a comprehensive pytest suite focused on:

- Provider-agnostic abstractions (MessagingAdapter)
- Loop adapter behavior (outbound payload shapes, inbound normalization)
- Webhook endpoint contract and signature verification
- Developer experience: fast, isolated, network-free tests by default

## Running tests

```
pip install -r requirements.txt
pytest -q
```

## Structure

- tests/test_health.py: Health checks
- tests/test_root.py: Root endpoint
- tests/test_loop_adapter.py: Unit tests for Loop adapter send/normalize
- tests/test_contract_loop_examples.py: Contract-style tests using documented Loop payload examples
- tests/test_webhook_flow.py: End-to-end webhook → agent → outbound send (mocked client)
- tests/test_signature_verification.py: Secret enforcement behavior

## Philosophy

- No external network calls in unit tests. HTTP calls are mocked/stubbed via test doubles.
- Deterministic defaults: environment isolated by conftest.py.
- High readability: clear given/when/then structure, explicit assertions, and minimal fixtures.
- Parity with production: shapes derive from LoopMessage-iMessage-API-Mock-Spec.md.

## Extending

To add new providers:

1. Implement a subclass of MessagingAdapter with normalize_inbound, send_message, and optional verify_signature.
2. Add provider-specific tests mirroring the Loop tests.
3. Wire a router for provider webhooks or extend existing webhook to route by header/path.

# Testing Strategy

This repository includes a comprehensive pytest suite focused on:

- Provider-agnostic abstractions (MessagingAdapter)
- Loop adapter behavior (outbound payload shapes, inbound normalization)
- Webhook endpoint contract and signature verification
- Developer experience: fast, isolated, network-free tests by default

## Running tests

```
pip install -r requirements.txt
pytest -q
```

## Structure

- tests/test_health.py: Health checks
- tests/test_root.py: Root endpoint
- tests/test_loop_adapter.py: Unit tests for Loop adapter send/normalize
- tests/test_contract_loop_examples.py: Contract-style tests using documented Loop payload examples
- tests/test_webhook_flow.py: End-to-end webhook → agent → outbound send (mocked client)
- tests/test_signature_verification.py: Secret enforcement behavior

## Philosophy

- No external network calls in unit tests. HTTP calls are mocked/stubbed via test doubles.
- Deterministic defaults: environment isolated by conftest.py.
- High readability: clear given/when/then structure, explicit assertions, and minimal fixtures.
- Parity with production: shapes derive from LoopMessage-iMessage-API-Mock-Spec.md.

## Extending

To add new providers:

1. Implement a subclass of MessagingAdapter with normalize_inbound, send_message, and optional verify_signature.
2. Add provider-specific tests mirroring the Loop tests.
3. Wire a router for provider webhooks or extend existing webhook to route by header/path.


