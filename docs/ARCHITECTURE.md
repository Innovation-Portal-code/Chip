# Architecture Overview

A modular FastAPI service that receives Loop Messaging webhooks, normalizes events, calls an agent to generate replies, and sends responses via the Loop REST API. The design is adapter-based to support additional providers (Twilio, WhatsApp) without changing core logic.

## Modules

- app/routers/loop_webhook.py: Webhook endpoint for Loop
- app/adapters/base.py: MessagingAdapter abstract base
- app/adapters/loop.py: Loop client and adapter (send + normalize)
- app/agents/dspy_agent.py: Agent entrypoint (stub; swap with DSPy+Groq)
- app/models/messages.py: Provider-agnostic message models
- app/config.py: Lightweight settings

## Flow

1. Loop → POST /webhooks/loop
2. Router verifies signature (optional), normalizes payload via adapter
3. Agent generates a reply text
4. Adapter sends message back to Loop using consolidated send endpoint

## Extending Providers

Implement a new adapter subclassing MessagingAdapter and wire a new router or route by path/header. Mirror Loop tests to ensure parity.