## Research: Building a Text-Only, Long-Term Conversational AI Agent (2025)

This document is a practical, expert-level playbook for designing, implementing, and operating a text-only conversational AI product that communicates via iMessage, WhatsApp, MMS, and SMS. It also covers observability, workflow orchestration, agent frameworks, and modern API design with an emphasis on long-term, contextual, and personalized experiences at scale.

The agent’s product goals assumed here:
- Connect users based on shared interests and make double-opt-in introductions
- Serve as a career coach and sounding board
- Alert users about relevant local events
- Suggest networking activities to help users advance in their careers
- Maintain a consistent, evolving personality that adapts per-user over time

Contents
- Messaging channels: iMessage options, Twilio (SMS/MMS), WhatsApp
- Observability: Logfire and OpenTelemetry
- Workflow orchestration: Temporal
- AI agent framework: Pydantic AI
- Web framework: FastAPI
- Advanced topics: long-term conversational design, context engineering, vector search and embeddings-based recommendations, event-driven architecture
- Security, compliance, testing, and reliability
- Reference blueprints and example snippets
- Curated references


### Architecture at a glance

- Channel gateways: Webhook handlers for SMS/MMS (Twilio) and WhatsApp (Meta/Twilio). iMessage options discussed below.
- Conversation ingestion: Validate, normalize, enrich, and publish events (EDA). Persist raw transcripts.
- Orchestrator: Temporal workflows coordinate long-running conversations, scheduled follow-ups, nudges, and introductions.
- Agent service: Pydantic AI-based agent with tools for retrieval, recommendations, and actions (send message, create intro, schedule, etc.).
- Memory and retrieval: Vector database for semantic memory + relational store for user/profile/consents. Hybrid search.
- Observability: Logfire for structured logs and traces; OpenTelemetry interop across services.
- API: FastAPI with typed models, webhook verification, background tasks, and streaming when needed.


## Messaging Channels

### iMessage (current options and constraints)

Reality check (2025): Apple does not provide a general-purpose public server-side API for iMessage. Options:
- Apple Messages for Business (formerly Business Chat): Official B2C channel with approved providers. It is not generic iMessage; requires Apple review, specific use cases, and customer-facing integrations.
- macOS relay approaches (not recommended for production): Automate the Messages app on a dedicated Mac via AppleScript/Private frameworks, or bridge software (e.g., community tools). These approaches are brittle, have significant security, privacy, and reliability risks, and can break with OS updates. They also raise compliance concerns and are inappropriate for most commercial deployments.
- Strategy recommendation: Use SMS/MMS (Twilio) and WhatsApp for reliable, compliant messaging. If you truly need Apple channels, evaluate Messages for Business via an approved provider and ensure your use case aligns with Apple policies.

Key considerations if you still explore a macOS relay:
- Security: Treat the Mac as a hot secret store; harden it, restrict network, rotate credentials, and monitor aggressively.
- Compliance: Understand the privacy implications and clearly disclose to users. Many enterprises will not accept this.
- Reliability: Expect breakage on OS updates; build health checks and fallbacks (e.g., failover to SMS with user consent).


### Twilio (SMS/MMS)

Core capabilities
- Programmable Messaging for SMS/MMS and the Conversations API for multi-participant threads
- Global reach with carrier-specific constraints
- Delivery callbacks, status tracking, media attachments, and phone number management

Operational best practices (production-grade)
- Compliance and registration: In the U.S., register A2P 10DLC (or use toll-free/short codes). Comply with TCPA, CTIA guidelines, and maintain STOP/HELP flows.
- Webhook security: Validate `X-Twilio-Signature` using Twilio’s RequestValidator. Reject requests that fail signature validation.
- Throughput and rate limits: Use Messaging Services and number pools; implement queueing with backoff; handle 429s and carrier filtering gracefully.
- Content rules: Avoid spammy content; include brand identification and opt-out instructions; keep message length appropriate (GSM segmentation limits); prefer links with branded domains.
- Media (MMS): Validate media types; compress images; include captions; host media reliably with HTTPS.
- Error handling: Inspect `MessageStatus` and error codes; implement retries where safe; route around failing carriers if necessary.
- Data privacy: Never log message bodies verbatim in production logs; tokenize/redact; adhere to retention minima.

FastAPI: inbound webhook handler (SMS)
```python
from fastapi import FastAPI, Request, HTTPException
from twilio.request_validator import RequestValidator

app = FastAPI()

TWILIO_AUTH_TOKEN = "<env>"
validator = RequestValidator(TWILIO_AUTH_TOKEN)

@app.post("/twilio/webhook")
async def twilio_webhook(request: Request):
    # Twilio posts as application/x-www-form-urlencoded
    body = await request.body()
    form = dict((await request.form()).items())

    signature = request.headers.get("X-Twilio-Signature")
    url = str(request.url)
    if not signature or not validator.validate(url, form, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    from_number = form.get("From")
    body_text = form.get("Body", "")
    media_url = form.get("MediaUrl0")  # optional

    # Publish an event to your message bus or call your orchestrator
    # e.g., enqueue_message({"channel":"sms","from":from_number,...})
    return {"ok": True}
```

Sending SMS/MMS (server-initiated)
```python
from twilio.rest import Client

client = Client("<account_sid>", "<auth_token>")

def send_sms(to: str, body: str) -> str:
    msg = client.messages.create(
        messaging_service_sid="<msg_service_sid>",
        to=to,
        body=body,
    )
    return msg.sid

def send_mms(to: str, body: str, media_urls: list[str]) -> str:
    msg = client.messages.create(
        messaging_service_sid="<msg_service_sid>",
        to=to,
        body=body,
        media_url=media_urls,
    )
    return msg.sid
```


### WhatsApp (via Meta Graph API or Twilio)

Key concepts
- Session vs Template messages: Free-form within 24h of user’s last message; outside 24h requires approved templates.
- Templates: Category (e.g., utility, marketing), variables, and locale; keep quality score healthy.
- Interactive messages: Buttons, lists, location; media and document support.
- Opt-in and consent: Explicit user opt-in is required; maintain opt-out mechanisms.

Webhook verification and inbound messages (Meta)
```python
from fastapi import FastAPI, Request

app = FastAPI()
VERIFY_TOKEN = "<env>"

@app.get("/whatsapp/webhook")
async def verify(mode: str | None = None, challenge: str | None = None, token: str | None = None):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge) if challenge and challenge.isdigit() else challenge
    return "forbidden"

@app.post("/whatsapp/webhook")
async def inbound(request: Request):
    payload = await request.json()
    # Validate signature header if configured
    # Extract messages and publish to your orchestrator
    return {"ok": True}
```

Sending a text via Meta Graph API
```python
import httpx, os

GRAPH_URL = "https://graph.facebook.com/v20.0"
PHONE_NUMBER_ID = os.getenv("WA_PHONE_ID")
ACCESS_TOKEN = os.getenv("WA_ACCESS_TOKEN")

async def send_whatsapp_text(to_e164: str, text: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{GRAPH_URL}/{PHONE_NUMBER_ID}/messages",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to_e164,
                "type": "text",
                "text": {"body": text},
            },
        )
        r.raise_for_status()
        return r.json()
```

If using Twilio for WhatsApp: sending is similar to SMS using a `from_='whatsapp:+<number>'` sender; you still must respect template rules.


## Observability with Logfire (and OTel)

Why Logfire here
- Python-native developer experience with structured logs, traces, and integrations for FastAPI and Pydantic AI
- Built-in redaction helpers and context fields; compatible with OpenTelemetry exporters

Best practices
- Structured logging: Use event-style logs with consistent keys. Include correlation ids (request id, user id, conversation id, workflow id).
- Redaction: Never log PII or message content in plaintext; store hashed/tokenized references. Use Logfire’s redaction to scrub fields.
- Tracing: Instrument FastAPI, background workers, and Temporal activities. Propagate trace context across async boundaries.
- SLOs and dashboards: Track golden signals (latency, errors, saturation, traffic) per endpoint and workflow. Create alerts tied to business metrics (e.g., intro success rate).

FastAPI + Logfire minimal setup
```python
import logfire
from fastapi import FastAPI

app = FastAPI()
logfire.configure(service_name="ai-agent-api", environment="prod")
logfire.instrument_fastapi(app)

@app.get("/health")
async def health():
    logfire.info("healthcheck", component="api")
    return {"ok": True}
```

Pydantic AI + Logfire
```python
import logfire

logfire.configure(service_name="agent", environment="prod")
logfire.instrument_pydantic_ai()
```

OpenTelemetry interop
- Export traces/metrics to your APM if needed. Align resource attributes (service.name, env, version) across services to enable cross-service tracing.


## Workflow Orchestration with Temporal

Concepts
- Workflow: Durable, deterministic code that models a long-running business process (e.g., multi-week coaching). Survives restarts.
- Activity: External side-effecting operation (send SMS, write DB, call model). Retries with backoff; must be idempotent.
- Signals/Queries: Async inputs into a running workflow (e.g., inbound user messages) and read-only introspection.
- Timers/Schedules: Sleep/delay; cron-like schedules for nudges, weekly recaps, or event reminders.
- Versioning: Guard workflow code changes for in-flight executions.

Patterns worth using
- Conversation workflow per user (or per conversation): Receives Signals from inbound messages; controls cadence; sets reminders; records state transitions.
- SAGA for multi-step actions (e.g., arranging an introduction) with compensations (cancel invites, notify participants).
- Outbox + idempotency keys: Ensure exactly-once semantics for activities like sending messages.
- Human-in-the-loop: Pause on uncertain decisions; resume via Signals from a review tool.

Python SDK example (simplified)
```python
from temporalio import workflow, activity

@activity.defn
async def send_channel_message(payload: dict) -> None:
    # Call Twilio/Meta; must be idempotent based on payload["idempotency_key"]
    ...

@workflow.defn
class ConversationWorkflow:
    def __init__(self):
        self.history: list[dict] = []

    @workflow.run
    async def run(self, user_id: str):
        # On start, maybe send a welcome if allowed
        # Then wait for messages via signals indefinitely
        await workflow.wait_condition(lambda: False)  # placeholder; real impl uses signals

    @workflow.signal
    async def inbound(self, msg: dict):
        self.history.append(msg)
        # Decide next action; schedule activity calls or timers
        await workflow.execute_activity(
            send_channel_message,
            {"to": msg["from"], "text": "Thanks!"},
            start_to_close_timeout=30,
        )

    @workflow.query
    def summary(self) -> dict:
        return {"count": len(self.history)}
```

Operational tips
- Keep workflows deterministic; avoid reading clocks or randomness without workflow APIs.
- Activities should be short, side-effecting, and idempotent; add retries and timeouts.
- Use Search Attributes to filter/find workflows (e.g., by user_id, channel, region).
- Carefully manage versioning to avoid breaking in-flight executions.


## Pydantic AI (agent runtime)

What it’s great for
- Strongly-typed tool schemas and inputs/outputs using Pydantic v2
- Seamless observability with Logfire
- Clean integration with FastAPI and async Python

Agent design patterns
- Tools as first-class citizens: Define capabilities (send_message, retrieve_profile, recommend_intro) with strict types.
- Memory interfaces: Provide the agent with a memory layer (semantic + episodic). Use retrieval tools for RAG across user notes, transcripts, and event data.
- Personality: Load a consistent persona prompt with guardrails and style; allow per-user style adjustments.
- Safety: Add moderation tools; disallow certain actions; require confirmations for sensitive steps (like introductions) via function-calling flows.

Minimal agent sketch
```python
from pydantic import BaseModel, Field
# from pydantic_ai import Agent  # use the library's Agent class per docs

class IntroRequest(BaseModel):
    seeker_user_id: str
    topic: str

class IntroPlan(BaseModel):
    message_to_a: str
    message_to_b: str
    requires_opt_in: bool = True

def recommend_intro(req: IntroRequest) -> IntroPlan:
    # Lookup embeddings, find candidate matches, craft messages
    return IntroPlan(
        message_to_a=f"Would you like an intro about {req.topic}?",
        message_to_b=f"Are you open to meeting someone about {req.topic}?",
    )

# agent = Agent(model="<provider>:<model>", system_prompt="...persona...")
# agent.register_tool("recommend_intro", recommend_intro, IntroRequest, IntroPlan)
```

Observability
- Enable Logfire instrumentation for spans per tool call and completion, including token usage and latency. Redact user content per policy.


## FastAPI (API surface)

Recommended structure
- App factory pattern with settings loaded via Pydantic Settings
- Dependencies for DB/session, auth, and request-scoped IDs
- Separate routers for webhooks (`/twilio`, `/whatsapp`), agent API, health, and admin

Performance & reliability
- Run with `uvicorn` (or `gunicorn` + `uvicorn.workers.UvicornWorker`)
- Timeouts and circuit breakers for outbound calls
- BackgroundTasks for fire-and-forget flows; for durable tasks, prefer Temporal
- Validate and limit payload sizes; return quickly to webhooks (ack then process async)

Security
- Validate Twilio signatures and WhatsApp verify tokens
- Rate limit and bot-protect public endpoints
- Strict CORS only if required


## Advanced Topics

### Long-term conversational design

Memory taxonomy
- Working memory: short-lived conversation window
- Episodic memory: durable summaries of past interactions
- Semantic memory: facts about the user, preferences, goals, entities
- Procedural memory: how-tos and policies for agent behavior

Techniques
- Progressive summarization: After N turns, distill to updates that feed semantic memory; keep raw transcript elsewhere
- Time-decay and pinning: Decay low-value memories; pin high-signal facts
- Double opt-in introductions: Always get consent from both parties before connecting; include context and safety tips
- Event relevance: Use geo/time filters and embeddings to map events to interests; surface a small, high-quality set
- Tone and persona: Establish a core persona with adjustable style knobs per user (formality, enthusiasm, brevity)

Safety and ethics
- Content moderation (input and output), escalation to human reviewers on edge cases
- Avoid over-claiming capabilities; be transparent when uncertain
- Bias and fairness: Monitor recommendation diversity; avoid echo chambers


### Context engineering

RAG pipeline design
- Ingestion: chunking strategies (semantic, separator-based), metadata (time, source, user)
- Indexing: vector DB with filters; MMR or re-ranking for diversity
- Query planning: classify intent (answer, recommend, introduce, retrieve policy), then construct retrieval queries
- Grounding and citations: Include source titles and links; allow the agent to quote relevant snippets

Memory compression
- Periodic summarization with templates; maintain a rolling "profile card" per user
- Keep embeddings of summaries to enable fast semantic recall

Evaluation
- Offline: information recall tests, hallucination rate, citation accuracy
- Online: CSAT, resolution rate, intro acceptance rate, retention, message latency


### Vector search and embeddings-based recommendations

Design choices
- Embeddings: Choose high-quality text embeddings; consider domain-specific finetunes if necessary
- Indexing: IVF/PQ or HNSW for scale; enable metadata filters (e.g., geo, skills)
- Hybrid search: Combine lexical BM25 and semantic vectors; re-rank top-K
- Freshness: Store timestamps and boost recency for events/opportunities

Matching and intros
- User-interest bipartite graph + vector similarity for semantic closeness
- Multi-objective ranking: balance relevance, diversity, and novelty; enforce fairness constraints
- Feedback loops: Thumbs-up/down and follow-through signals feed bandits or RL to personalize

Metrics
- Offline: NDCG@K, MRR, coverage, diversity
- Online: conversion to conversation, intro acceptance, RSVP rates


### Event-driven architecture (EDA)

Principles
- Loose coupling via events; services consume what they need
- Idempotency and deduplication using event ids and outbox pattern
- Backpressure handling and DLQs; replay support for recovery

Patterns
- Outbox/Inbox: Persist events in the same transaction as state changes; separate dispatcher ships to the bus
- Schema registry and versioned contracts; additive changes first
- Exactly-once semantics are an illusion; design for at-least-once with idempotent consumers
- Correlate events with trace and conversation ids

Temporal + EDA
- Webhook handlers publish events; signals feed workflows that own durable state and timers
- Workflows emit events for downstream analytics and notifications


## Security, Compliance, Testing, Reliability

Security & privacy
- Secrets management: Use a vault; rotate credentials; least-privilege IAM
- Data minimization: Store only what you need; encrypt at rest and in transit
- PII: Tokenize/redact in logs; implement data subject rights (export/delete)

Messaging compliance
- SMS/MMS (U.S.): A2P 10DLC registration; STOP/HELP; quiet hours where applicable; avoid SHA links and spam terms
- WhatsApp: Obtain opt-in; template approvals for outside-24h messages; monitor quality rating and phone status
- Apple: Use Messages for Business only if qualified; otherwise avoid unofficial relays in production

Testing
- Contract tests for webhooks (Twilio signature, WhatsApp verification)
- Golden transcript tests for agent behavior with deterministic seeds
- Load testing for spikes (campaigns, event alerts)
- Chaos experiments on retries, partial outages, and timeouts

Reliability & cost controls
- Retries with jittered backoff; circuit breakers and budgets for LLM calls
- Cache deterministic prompts/results where safe; batch embeddings
- Autoscale workers; separate hot paths (webhooks) from slow paths (LLM/tooling)


## Reference blueprints

Message flow (SMS example)
1) Twilio -> FastAPI webhook (validate signature, enqueue event)
2) Event -> Temporal signal to ConversationWorkflow(user_id)
3) Workflow -> Agent tool calls (recommendations, memory updates)
4) Workflow -> Activity to send SMS reply (idempotent)
5) Logs/traces -> Logfire + APM

Service boundaries
- api-gateway: FastAPI webhooks and admin APIs
- orchestrator: Temporal workers hosting workflows and activities
- agent: Pydantic AI runtime and tools
- memory: vector DB + relational DB
- analytics: stream processing and warehouse


## Curated references

- Twilio Programmable Messaging: https://www.twilio.com/docs/sms
- Twilio WhatsApp: https://www.twilio.com/docs/whatsapp
- Meta WhatsApp Business Cloud API: https://developers.facebook.com/docs/whatsapp
- Pydantic Logfire docs: https://docs.pydantic.dev/logfire/ and https://logfire.pydantic.dev
- Temporal docs: https://docs.temporal.io
- FastAPI docs: https://fastapi.tiangolo.com
- Context engineering (overview): https://aakashgupta.medium.com/context-engineering-the-evolution-beyond-prompt-engineering-thats-revolutionizing-ai-agent-0dcd57095c50
- Vector DBs and hybrid search (Weaviate, Pinecone, FAISS): see respective vendor docs; evaluate based on scale, latency, and filters


—
This guide favors reliability, safety, and compliance by steering production use toward officially supported channels (SMS/MMS, WhatsApp) with Temporal for durability, Pydantic AI for typed agents, FastAPI for APIs, and Logfire/OTel for visibility. If you need deeper implementation detail (e.g., specific vendor SDK code), annotate the sections you want expanded and we’ll enrich with runnable examples.

