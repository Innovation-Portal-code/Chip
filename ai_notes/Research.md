## Research: Building a Text-Only, Long-Term Conversational AI Agent (2025)

This document is a research-based reference for architects and planners to design, implement, and operate a text-only conversational AI system that communicates via iMessage, WhatsApp, MMS, and SMS. It covers observability, workflow orchestration, agent frameworks, and modern API design with an emphasis on long-term, contextual, and personalized experiences at scale.

The agent’s product goals assumed here are concrete and user-centered. At its core, the agent connects people based on shared interests and facilitates introductions only after both parties explicitly consent, a practice known as double opt-in that protects user autonomy and trust. Beyond introductions, the agent functions as a career coach and sounding board that can nudge, advise, and reflect with users as they progress through goals and decisions. It also operates as a personalized local guide, alerting users to events and opportunities in their area that align with their interests, availability, and consented preferences. To close the loop, the agent suggests networking activities designed to help users advance in their careers through lightweight, contextual prompts that encourage action. Across all of these interactions, the agent maintains a consistent, evolving personality that adapts to each user over time, so that style, tone, and pacing feel familiar and supportive rather than generic or erratic.

How to use this reference: treat the document as a planning aid and design reference rather than a step-by-step tutorial. Each section is written to stand alone so that you can adopt the parts that match your constraints without dragging in unrelated complexity. Code snippets are intentionally focused on interfaces and patterns; adapt them to your stack, harden them with tests, and align them with your security and compliance policies before deploying to production.

Contents
- Messaging channels: iMessage options, Twilio (SMS/MMS), WhatsApp
- Observability: Logfire and OpenTelemetry
- Workflow orchestration: Temporal
- AI agent framework: Pydantic AI
- Web framework: FastAPI
 - Infrastructure: Railway
 - Types and type safety (first-class)
 - Software engineering patterns
 - Database: Supabase (pgvector + relational)
 - Tooling: uv (deps/env)
- Advanced topics: long-term conversational design, context engineering, vector search and embeddings-based recommendations, event-driven architecture
- Security, compliance, testing, and reliability
 - Security
 - Compliance
 - Testing
 - Reliability
 - DSPy for prompt/workflow optimization
 - Production-grade software considerations
- Reference blueprints and example snippets
- Curated references


### Architecture at a glance

This system is intentionally split into clear, independently evolvable subsystems that reflect the realities of long-lived conversations, multi-channel delivery semantics, and safety/compliance constraints. In practice, every inbound message from any channel is immediately validated and normalized into a single event shape, then written durably before any business logic fires. That durable write becomes the contract between the outside world and the inside of the platform: it allows us to replay conversations, debug issues, and test new agents against historical transcripts without touching the channel edge. Downstream, an orchestrator—the Temporal workers—own the durable program that decides what to do next: whether to acknowledge receipt, ask a clarifying question, summon retrieval from memory, propose an introduction, or schedule a follow-up nudge next Tuesday at 9 am. The agent service is the reasoning and tool-using brain; it never talks directly to the world. Instead, it consumes typed inputs and produces typed outputs that are easy to test, observe, and version. Memory is not an afterthought: we persist both raw transcripts and structured summaries, maintain embeddings that let us find semantically related history, and store user preferences, consents, and network graphs that enable introductions. Observability spans everything—logs, metrics, and traces stitch together an end-to-end picture across webhooks, workflows, agent calls, and database interactions so that production issues are diagnosable within minutes rather than hours. At the edges sit channel gateways that receive webhooks for SMS/MMS and WhatsApp while handling iMessage through the options discussed below; the gateways feed a conversation ingestion layer that validates, enriches, and publishes events while persisting raw transcripts. Durable orchestration is handled by Temporal workflows that coordinate long-running conversations, scheduled follow-ups, nudges, and introductions, and a Pydantic AI-based agent service provides typed tools for retrieval, recommendations, and actions. Memory spans a vector database for semantic recall alongside a relational store for users, profiles, and consents, with hybrid search to combine the two; observability integrates Logfire for structured logs and traces with OpenTelemetry for cross-service interoperability. The API surface, implemented with FastAPI, exposes typed models, webhook verification, background tasks, and optional streaming while keeping business logic decoupled from transport concerns.


## Messaging Channels

### iMessage (current options and constraints)

In the context of a multi-channel conversational system, iMessage is both a differentiator and a volatility source. It is a differentiator because the conversation arrives in a familiar, trusted environment for iPhone users with rich features like reactions, read receipts, and seamless media—features that meaningfully improve first-contact conversion and subsequent retention. It is a volatility source because there is no general-purpose, officially supported server API; every integration relies on either Apple Business Messaging (with a specific qualified use case and approved provider) or a macOS-hosted bridge that drives the first-party Messages client on your behalf. The correct architectural posture is to treat iMessage as a valuable, high-conversion front door that is nevertheless surrounded by guard rails: strict health monitoring, clear fallbacks, explicit user transparency, and layered security controls around any relay host that could process user content. This posture balances UX ambitions with operational realism.

Reality check (2025): Apple does not provide a general-purpose public server-side API for iMessage. In practice, this leaves two categories of approach: Apple Messages for Business (formerly Business Chat), which is an approved B2C channel mediated by providers and suitable only for specific, Apple-vetted use cases; and macOS relay approaches that drive the first-party Messages client on a dedicated Mac via AppleScript, private frameworks, or third-party bridges. The former is official but constrained and not equivalent to generic iMessage; the latter is brittle, carries security and privacy risks, can break with OS updates, and is generally inappropriate for commercial deployments. The pragmatic posture is to rely on SMS/MMS and WhatsApp for reliable, compliant messaging and to consider Messages for Business only if your use case squarely fits Apple’s policies and you can work with an approved provider.

If you nevertheless explore a macOS relay, treat the host as a high-sensitivity boundary: harden the machine, restrict its network egress, rotate credentials frequently, and monitor aggressively as if it were a hot secret store. Be explicit about privacy implications and disclosures, recognizing that many enterprises will not accept this model, and plan for reliability hazards such as OS updates that can break automation by building health checks, idempotent send logic, and clear fallbacks—typically a user-consented failover to SMS.


### LoopMessage (iMessage channel)

LoopMessage provides a server-facing API to send and receive iMessages (with support for SMS fallback strategies you control). It exposes webhooks for inbound messages and send/delivery status updates, reactions, and group conversations.

LoopMessage adds a server-facing abstraction for iMessage delivery and receipt, supporting text and attachments to Apple IDs and phone numbers while preserving the rich interaction surface of the channel. Beyond simple sends, it supports reactions (tapbacks), audio and image/video messages, and the constructs needed for reply threads and group chats. Operationally, it publishes webhooks with `alert_type` values such as `message_inbound`, `message_sent`, `message_failed`, `message_scheduled`, `message_timeout`, `message_reaction`, `conversation_inited`, `group_created`, and `inbound_call`, enabling a fully event-driven integration. While iMessage remains end-to-end encrypted between devices, any macOS relay or provider agent you use to bridge server-side logic to the client must be treated as a privileged boundary and hardened accordingly.

A pragmatic reliability strategy starts with progressive fallback: prefer iMessage when available, but on explicit failures, timeouts, or unreachable devices, degrade to SMS via Twilio—or to WhatsApp if the user has consented to that channel—and make this behavior transparent to users to preserve trust. Protect against duplication by attaching an idempotency key to every send so that retried or fallback deliveries can be safely de-duplicated downstream. Maintain per-user channel preferences, including quiet hours and regional rules, and continuously monitor the health of any macOS relay or provider agent with heartbeats and alerting so you can automatically drain traffic to SMS if health degrades. Persist send attempts, statuses, and fallback decisions to create an auditable trail for support and post-incident analysis.

Typed webhook example (LoopMessage)
```python
from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional, List

AlertType = Literal[
    "message_scheduled",
    "conversation_inited",
    "message_failed",
    "message_sent",
    "message_inbound",
    "message_reaction",
    "message_timeout",
    "group_created",
    "inbound_call",
    "unknown",
]

MessageType = Literal["text", "reaction", "audio", "attachments", "sticker", "location"]
DeliveryType = Literal["imessage", "sms"]
ReactionType = Literal["love", "like", "dislike", "laugh", "exclaim", "question", "unknown"]

class Language(BaseModel):
    code: str
    name: Optional[str] = None
    script: Optional[Literal["Hans", "Hant"]] = None

class SpeechMetadata(BaseModel):
    speaking_rate: Optional[float] = None
    average_pause_duration: Optional[float] = None
    speech_start_timestamp: Optional[float] = None
    speech_duration: Optional[float] = None
    jitter: Optional[float] = None
    shimmer: Optional[float] = None
    pitch: Optional[float] = None
    voicing: Optional[float] = None

class Speech(BaseModel):
    text: str
    language: Optional[Language] = None
    metadata: Optional[SpeechMetadata] = None

class Group(BaseModel):
    group_id: str
    name: Optional[str] = None
    participants: List[str] = []

class WebhookEvent(BaseModel):
    alert_type: AlertType
    recipient: Optional[str] = None
    text: Optional[str] = None
    subject: Optional[str] = None
    attachments: Optional[List[HttpUrl]] = None  # only for message_inbound
    message_type: Optional[MessageType] = None   # inbound/reaction
    delivery_type: Optional[DeliveryType] = None
    reaction: Optional[ReactionType] = None      # only for message_reaction
    thread_id: Optional[str] = None
    sandbox: Optional[bool] = None
    sender_name: Optional[str] = None
    error_code: Optional[int] = None             # failed/timeout
    passthrough: Optional[str] = None
    language: Optional[Language] = None
    group: Optional[Group] = None                # only for group_created
    speech: Optional[Speech] = None              # inbound audio transcription
    success: Optional[bool] = None               # only for message_sent
    message_id: Optional[str] = None
    webhook_id: Optional[str] = None
    api_version: Optional[str] = None
```

Sample webhook events (per LoopMessage docs)
```json
{
  "alert_type": "message_inbound",
  "recipient": "+13231112233",
  "text": "text",
  "message_type": "text",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```

```json
{
  "alert_type": "message_sent",
  "success": true,
  "recipient": "+13231112233",
  "text": "text",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```

```json
{
  "alert_type": "group_created",
  "group": {
    "group_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
    "name": "Group name",
    "participants": ["+13231112233", "+13233332211", "[email protected]"]
  },
  "recipient": "+13231112233",
  "sender_name": "[email protected]",
  "text": "text",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b"
}
```

Sending an iMessage via LoopMessage
```python
import httpx

async def send_imessage(recipient: str, text: str, *, idempotency_key: str) -> dict:
    headers = {
        "Authorization": "Bearer <token>",
        "Loop-Secret-Key": "<secret>",
        "Idempotency-Key": idempotency_key,
        "Content-Type": "application/json",
    }
    data = {"recipient": recipient, "text": text}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://server.loopmessage.com/api/v1/message/send/",
            headers=headers,
            json=data,
        )
        r.raise_for_status()
        return r.json()
```

Group chats and thread continuity depend on stable identifiers: use the `group.group_id` for group chats (you can use this value as the contact/recipient in send requests) and, when present, the `thread_id` from webhook payloads to maintain reply-to context. Keep participant rosters current so that consented introductions and multi-party conversations honor membership and privacy expectations across joins and leaves.

Operational security should treat the macOS relay or provider agent as a privileged boundary with restricted console and log access. Avoid storing message bodies in plaintext logs; rotate credentials regularly; prefer hardware-backed secrets; enforce strict SSH key policies; and monitor for configuration drift and OS updates that could weaken your posture or break integration.

### Twilio (SMS/MMS)

Twilio remains the backbone of global messaging because it abstracts an unruly mesh of carrier interconnects, geo-specific regulations, throughput quirks, and handset behaviors into a consistent developer experience. Treat it as a utility layer that provides reach, delivery transparency, and compliance controls, while recognizing that carriers are not identical and outcomes will vary by geography, route, and content. For a product built on trust, two things matter most: design for the happy path with crisp content and clear opt-in/opt-out mechanics, and design for unhappy paths with robust retries, delivery status auditing, and user-friendly fallbacks. Twilio’s Messaging Services, A2P 10DLC registration (in the U.S.), and compliance tooling give you levers to protect your deliverability and brand reputation. Build programmatic guard rails around those levers, and surface telemetric signals—filtered/undelivered spikes, 3xx/4xx error codes, throughput throttles—into your observability system so that the on-call engineer can reason about incidents quickly.

Another pragmatic consideration is message economics and latency. Carriers sometimes silently filter or delay content that appears spammy, includes risky links, or violates local norms (e.g., quiet hours). Keep copy short and declarative, brand your links (avoid random URL shorteners), and use conversational templates that disclose sender and opt-out instructions. Aggregate delivery receipts to measure per-number, per-country, and per-carrier performance. When feasible, split high-volume sends across number pools under a Messaging Service to smooth throughput peaks and minimize carrier throttling. When interacting conversationally, however, prefer a consistent sender for each user—churned numbers harm continuity. The right balance is often: a dedicated number (or small pool) per locale for conversational flows, and a larger pool for one-way notifications under strict rate control.

Core capabilities span Twilio’s Programmable Messaging for SMS and MMS alongside the Conversations API that models multi-participant threads with message continuity. The platform offers global reach that abstracts the complexity of carrier-specific constraints while still surfacing the operational differences you must account for in production. Delivery callbacks and status tracking provide observability for each message’s lifecycle, media attachments enable richer interactions across devices and routes that support them, and comprehensive phone number management lets you provision, pool, and retire numbers in a way that balances throughput, deliverability, and brand consistency.

Operational best practices in production begin with compliance and registration. In the United States, A2P 10DLC registration is required for most application-to-person messaging on 10-digit long codes; alternatives include toll-free numbers or short codes where appropriate. Compliance with TCPA and CTIA guidelines is not optional and should be enforced by design, including reliable STOP and HELP flows that work even under partial system failure. Security at the webhook boundary is critical: validate the `X-Twilio-Signature` header using Twilio’s RequestValidator against the exact URL and form payload and reject any request that fails validation. Throughput and rate limits should be treated as a first-class performance envelope. Use Twilio Messaging Services and number pools to spread traffic appropriately, implement outbound queueing with exponential backoff, and handle HTTP 429s and known carrier filtering behaviors gracefully rather than retrying blindly. Content quality is not merely aesthetic: avoid spammy phrasing, identify your brand clearly, include opt-out instructions in conversational contexts, and respect GSM segmentation limits to prevent fragmentation or unexpected costs. When sending MMS, validate media types and sizes, compress images when possible, include succinct captions, and ensure that media hosting uses reliable, HTTPS endpoints that perform well globally. Error handling must go beyond catching exceptions—inspect `MessageStatus` transitions and provider error codes to decide when a retry is safe or when you should route around a failing carrier path. Above all, protect user privacy: never log message bodies verbatim in production, tokenize or redact sensitive fields, and enforce data retention policies that minimize exposure while preserving enough diagnostic information to support incident response.

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

WhatsApp imposes a distinct operational model compared to SMS: a 24-hour customer care window for free-form messaging after a user’s last message and template-based messages to reach users outside that window. This design serves both user control and platform quality, and it forces your system design to model intent and timing explicitly. As a result, you must treat WhatsApp as a stateful channel: track session windows, map user intents to pre-approved template categories (utility, authentication, marketing), and maintain a catalog of localized, parameterized templates. When a conversation is active, WhatsApp is an excellent two-way channel with rich media and interactive components (buttons, lists, locations). When dormant, you must use a template to restart the conversation, which implies your agent orchestrator needs to pick the right template, fill variables accurately, and back off if quality signals degrade.

Quality ratings and phone number status are critical. Overly aggressive or irrelevant templates, poor localization, and high user blocks or reports will degrade your sender quality and eventually limit your reach. Build feedback loops: track template performance by locale, vertical, and audience; use soft rollouts to new audiences; and retire underperforming templates. Inbound flows should respect opt-in provenance and present a consistent, human tone that matches your product’s persona: formal for compliance-heavy communications, light but respectful for coaching and community introductions. Above all, be transparent in cross-channel fallbacks: if you switch from WhatsApp to SMS for reliability reasons, tell the user why and how to opt back to their preferred channel.

Several operational concepts are essential to using WhatsApp well. The platform distinguishes between session messages and template messages, where the former are free-form within a 24‑hour “customer care” window following the user’s last message and the latter are pre-approved, structured messages used to reach users outside that window. Templates are categorized—common categories include utility, authentication, and marketing—parameterized by variables, and localized by locale codes; you must monitor and maintain a healthy quality score for each template and locale to preserve reach. Beyond plain text, WhatsApp supports interactive messages such as buttons and lists, along with rich media and document attachments, which allow you to build more expressive conversational flows. None of this is permissible without explicit opt-in and consent that you can demonstrate if audited; equally important is maintaining simple opt-out mechanisms and respecting user preferences across channels.

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

Observability has to be designed-in for conversational systems because the failure modes are frequently at the seams—between a webhook and a workflow, a workflow and an agent tool, or a tool and an external provider. Logfire excels here because it makes cross-cutting instrumentation straightforward: you can attach structured context (conversation_id, user_id, workflow_id, message_id) to every log and span without fighting your framework. The operational discipline we recommend is to annotate every boundary with a durable correlation id and to propagate that id across async tasks, HTTP calls, and workflow signals. When an incident occurs—say, a spike in undelivered WhatsApp templates after a content change—consistent correlation gives you a forensics path: from the inbound webhook to the normalization layer to the workflow decision to the specific template send attempt with its provider error code. This reduces mean-time-to-diagnosis and prevents flailing during on-call.

The other pillar is privacy. Conversational agents process sensitive content; production logs must not become a shadow data store. Use Logfire’s redaction facilities to strip or hash message bodies and PII fields. Log at the shape of events (type, size, metadata) and at decision boundaries (which template was chosen, which tool was invoked, why a fallback occurred) rather than the raw content. Pair logs with aggregated metrics—error rates, latency percentiles, tool call success rates, LLM token costs—so that you can set SLOs that reflect user experience. Finally, connect OpenTelemetry exporters if you already have an APM; ensure consistent `service.name`, `deployment.environment`, and `service.version` across the API, orchestrator, and agent services so distributed traces stitch correctly.

Logfire is chosen here because it provides a Python-native developer experience with first-class support for structured logs and tracing and offers direct integrations with popular frameworks like FastAPI and Pydantic AI. Its redaction helpers and request-scoped context fields enable you to attach meaningful metadata to every log and span—such as conversation identifiers, workflow identifiers, and user identifiers—without risking accidental exposure of sensitive content. Compatibility with OpenTelemetry exporters means you can forward traces and metrics to your preferred APM while keeping a consistent instrumentation model across services.

Practically, observability benefits from disciplined best practices. Treat structured, event-style logging as the default so that downstream analysis is resilient to free‑form text and ad hoc formatting, and include durable correlation identifiers such as request, user, conversation, and workflow ids on every record to make cross-service forensics straightforward. Redact aggressively: never log personally identifiable information or message bodies in plaintext, prefer hashed or tokenized references instead, and use Logfire’s redaction features to scrub sensitive fields at ingress. Apply tracing uniformly across FastAPI endpoints, background workers, and Temporal activities, and ensure that trace context is propagated across asynchronous boundaries so distributed traces remain intact. Finally, define service-level objectives that reflect user-perceived quality—latency, error rates, saturation, and traffic for key endpoints and workflows—and create dashboards and alerts that tie operational anomalies to meaningful product metrics such as introduction success rate, rather than alerting on raw counters alone.

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
Export traces and metrics to your preferred APM when needed, and align resource attributes such as `service.name`, environment, and version uniformly across services so cross‑service tracing remains coherent and navigable.


## Workflow Orchestration with Temporal

Temporal’s core promise—durable execution—frees you from the usual fragility of long-running, eventful processes. In the conversational domain, that translates to confidence that reminders fire next week even if a pod is rescheduled tonight, that retries don’t double-send, and that human-in-the-loop pauses won’t be lost when an API restarts. The most important design choice is to keep non-determinism at the edges: workflows should orchestrate; activities should perform side effects. Treat every activity as idempotent and bound by timeouts with exponential backoff. When you send a message, generate and persist an idempotency key before the activity call so a retried activity will not create duplicates downstream. When you need to change behavior, use workflow versioning gates to avoid breaking in-flight executions. Combine signals for inbound messages with queries for introspection so your ops dashboards can ask a running workflow for its current state without mutating it.

At scale, you should invest in search attributes that map to how you operate: user_id, channel, locale, and high-level conversation state (e.g., onboarding, coaching, introduction_pending). These attributes enable fast filtering in the Temporal UI and allow bulk operations (pausing a cohort, rolling out a nudge) to target exactly the right set. For schedules—weekly summaries, event digests, re-engagement nudges—prefer Temporal Schedules over cron external to the platform so that timing, retries, and jitter are first-class and observable in one place. Finally, consider how on-call humans interact: it’s often valuable to have an “override” signal that can force a workflow to skip or repeat a step, useful during incidents or manual customer support interventions.

Concepts
Workflows are durable, deterministic programs that model long-running business processes such as multi-week coaching conversations; they survive restarts and infrastructure churn because their state is persisted by the Temporal runtime. Activities are the units that perform external side effects—sending SMS via Twilio, writing to a database, or invoking a model—and they must be idempotent, bounded by timeouts, and retried with exponential backoff so that failures do not create duplicate effects. Signals and queries provide the controlled interface to a running workflow: signals deliver asynchronous inputs like inbound user messages or administrative overrides, while queries expose read-only introspection for dashboards and operators without mutating state. Timers and schedules allow workflows to sleep and resume or to execute on cron-like cadences, which is essential for reminders, weekly recaps, and event digests. Versioning gates protect in-flight executions when you evolve workflow code by enabling explicit branching so that old and new versions can run safely side by side.

Patterns worth using
A conversation workflow scoped to a user or conversation acts as the durable conductor that receives signals for inbound messages, controls cadence and guardrails, sets reminders, and records state transitions for later analysis. For multi-step actions like arranging an introduction, adopt a SAGA pattern so that each step has a defined compensation (cancel invitations, notify participants) if later steps fail, preserving system invariants without global transactions. Combine an outbox table with per-send idempotency keys to approximate exactly-once semantics for activities such as message dispatch, ensuring that retries do not create duplicates downstream. Incorporate human-in-the-loop pauses at decision points where model confidence is low; the workflow can wait for a signal from a review tool to resume, making safety and oversight part of the same durable program.

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
Determinism is non-negotiable for workflows: avoid reading system clocks or introducing randomness outside Temporal’s provided APIs so replays lead to identical results. Activities should be short-lived, side‑effecting, and idempotent with explicit retries and timeouts to contain failures and bound resource usage. Invest in Search Attributes that reflect how you operate—user identifiers, channel, region, and high-level conversation state—so that operators can filter and act on cohorts directly from the Temporal UI. When evolving behavior, treat versioning as a safety rail: gate code paths to avoid breaking in-flight executions and roll out changes gradually.


## Pydantic AI (agent runtime)

The agent is the narrative center of this system, but it must never become a ball of mud. Pydantic AI encourages disciplined agent construction by requiring that tools, inputs, and outputs be expressed with exact types. This leads to three tangible benefits. First, observability: when a tool fails, you know precisely which field violated which constraint, and Logfire can display both the schema and the error without exposing raw content. Second, testability: with type-checked function signatures, you can unit test tool behavior and dataset-driven integration tests without spinning up channels or workflows. Third, evolvability: you can introduce new tools or refine outputs (e.g., add a `confidence` field, deprecate an optional `tone`) behind versioned models while the rest of the system compiles against stable interfaces.

A pragmatic agent architecture is to structure the agent around a small set of capabilities—understand, retrieve, plan, act—each powered by tools that are pure functions over typed inputs. Memory access should also be mediated through typed tools, not raw SQL: for example, `retrieve_user_profile(user_id) -> UserProfile`, `retrieve_events(query: EventsQuery) -> list[Event]`, and `recommend_introductions(input: RecommendIntroInput) -> RecommendIntroOutput`. By treating memory retrieval and action dispatch as tools, you can track every call with spans and success/failure metrics, cap invocation budgets, and apply rate controls to external services (e.g., vector DB or Twilio). The system prompt becomes a governance layer rather than a dumping ground: it states persona, high-level policies, and constraints, while the actual operations flow through validated tool calls that you can inspect, test, and evolve.

What it’s great for
Pydantic AI excels when tool schemas and inputs/outputs are expressed as precise, strongly typed models using Pydantic v2. This structure makes misuses obvious at the boundary and supports clear failure modes tied to specific fields and constraints. The framework integrates seamlessly with Logfire so that every tool call and completion can be traced with token usage, latency, and redacted context. It also plays naturally with FastAPI and idiomatic async Python, making it straightforward to build systems where API endpoints validate payloads, forward typed work to agents, and observe outcomes without glue code.

Agent design patterns
Treat tools as first-class citizens by defining capabilities such as sending messages, retrieving profiles, or recommending introductions as strictly typed functions with clear inputs and outputs. Encapsulate memory behind interfaces that separate semantic and episodic layers and expose retrieval tools for RAG across user notes, transcripts, and event data; this avoids leaking storage details into prompts and makes behavior testable. Embed a consistent persona prompt with guardrails and stylistic guidance, and allow per-user style adjustments so that the agent’s voice aligns with user expectations. Finally, prioritize safety by wiring in moderation tools, forbidding disallowed actions outright, and requiring explicit confirmations for sensitive steps like initiating introductions, implemented via function-calling flows rather than brittle prompt text.

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
Enable Logfire instrumentation so that each tool call and completion is wrapped in a span that records latency, token usage, and structured context fields. Ensure redaction policies are enforced so user content and PII are never written to logs, and propagate correlation identifiers through agent calls to make cross-service traces coherent.


### Tools as MCPs: integrating the Model Context Protocol (MCP)

The Model Context Protocol (MCP) offers a standardized way for agents to discover, describe, and invoke external tools. In this architecture, treat MCP as the default contract for tool integration. Instead of writing bespoke adapters for each capability (web search, data retrieval, analytics, code execution), connect your agent to one or more MCP servers that publish a catalog of typed tools. This yields three durable advantages:
Consistency, because discovery, schema, and invocation are unified across providers and environments; composability, because a single agent can mount multiple MCP servers and choose tools dynamically based on policy, cost, and availability; and evolvability, because tools can be versioned or replaced server‑side without necessitating changes to agent code.

Installation (client capabilities)
```bash
pip install "pydantic-ai-slim[mcp]"
```

MCP client transports include Streamable HTTP, which connects to a remote MCP server that supports streaming responses and works well for networked services and backpressure‑sensitive tasks; Server‑Sent Events (SSE), which also connects over HTTP when an SSE interface is available and streaming is desired; and stdio, which launches a server as a subprocess and communicates over stdin/stdout, providing low‑latency isolation that is ideal for local, sandboxed tools such as a “Run Python” server.

Minimal MCP client wiring
```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

server = MCPServerStreamableHTTP("http://localhost:8000/mcp")
agent = Agent("openai:gpt-4o", toolsets=[server])
# The agent can now discover and call tools exposed by the MCP server.
```

Agents within MCP servers
You can embed a Pydantic AI agent inside an MCP server so other clients can invoke agent-backed tools. This enables multi-agent systems where an orchestration agent delegates to a specialized agent via MCP.
```python
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent

server = FastMCP("Pydantic AI Server")
server_agent = Agent("anthropic:claude-3-5-haiku-latest", system_prompt="always reply in rhyme")

@server.tool()
async def poet(theme: str) -> str:
    """Poem generator using an embedded Pydantic AI agent"""
    r = await server_agent.run(f"write a poem about {theme}")
    return r.output

if __name__ == "__main__":
    server.run()
```

MCP Sampling
Some workflows require an MCP server to call a model while serving a client request. MCP Sampling formalizes this by allowing the server to call back to the client for inference. Use this for tight feedback loops—e.g., retrieval that requests a short-lived summary from the client’s model to refine the next query—while keeping trust boundaries explicit.

Concurrency and tool execution
When a model produces multiple tool calls in one response, Pydantic AI schedules them concurrently: asynchronous functions run on the event loop, synchronous functions are offloaded to threads. Prefer async tool implementations to avoid blocking; guard sync tools with thread-pool limits. Apply budgets and rate limits per toolset (and per MCP server) to control cost and protect downstream services. Wrap each tool call with Logfire spans that capture tool name, payload size, outcome, and latency—with sensitive fields redacted.

Governance and schema design
Define tool interfaces—local and MCP-exposed—with precise Pydantic models for inputs/outputs. Document versioning and deprecation policy (additive changes first; breaking changes behind a `version` field or new tool name). For MCP tools, keep JSON Schema descriptors current so clients can validate pre-execution. Combine allowlists/denylists with per-tool authentication (tokens, scopes) to enforce least privilege.


## FastAPI (API surface)

FastAPI functions as the contract layer of the platform, the front door through which channels submit webhooks and operators invoke admin actions. Its value is in type safety at the edge: every inbound payload is parsed into a Pydantic model before any logic runs, giving you an early “fail closed” mechanism against malformed or malicious requests. A well-structured FastAPI app also imposes clarity: routers keep channel webhooks separate from admin or analytics; dependencies inject database sessions, registries, and settings; response models make it impossible to accidentally leak internal fields. Because the system is event-driven, most endpoints should return quickly—acknowledge receipt, enqueue durable work, and let workflows proceed asynchronously. For rare synchronous flows (e.g., webhook challenge verification), keep the code paths tiny and completely side-effect-free.

Operationally, the choice of ASGI server matters for performance and protocol support. Uvicorn is a stellar default—fast, widely used, easy to run under Gunicorn—and Hypercorn is the flexible alternative when HTTP/2 or HTTP/3 (QUIC) is required or when you prefer the Trio concurrency model. Benchmark both in your environment under realistic concurrency and payload sizes; the winner should be adopted per service rather than dogmatically across the entire fleet. Finally, clarify local developer experience: we recommend `uv` to manage dependencies and environments via `pyproject.toml`, fast locks, and reproducible builds. Document common workflows—running the API with reloading, seeding the database, mocking channel webhooks—so onboarding engineers can be productive in an hour, not a week.

A maintainable FastAPI app benefits from an application factory that constructs the app with environment-specific settings loaded via Pydantic Settings so configuration remains explicit and testable. Common cross-cutting concerns such as database sessions, authentication, and request-scoped identifiers should be provided through dependency injection rather than globals, which keeps handlers pure and composable. Separating routers by concern—for instance, dedicating one router to webhooks like `/twilio` and `/whatsapp`, another to the agent API, and others to health checks and admin operations—preserves clarity at the API boundary and avoids accidental coupling.

For performance and reliability, the choice of ASGI server and worker model should be driven by your protocol and concurrency needs. Uvicorn is a fast, widely used default that pairs well with Gunicorn workers, while Hypercorn offers flexible support for HTTP/2 and HTTP/3 with multiple concurrency backends including asyncio, uvloop, and trio. Regardless of server, impose timeouts and circuit breakers on outbound calls so a slow dependency cannot exhaust resources. Use FastAPI’s BackgroundTasks for short, fire‑and‑forget operations, and delegate durable, long-running tasks to Temporal where retries and time budgets are explicit. Validate and bound payload sizes at the edge to avoid amplification attacks, and design webhook routes to acknowledge quickly and defer heavy work to internal queues or workflows.

Security at the edge should validate Twilio signatures and WhatsApp verification tokens to ensure only genuine providers can call your webhooks. Rate limit and bot-protect public endpoints to blunt automated abuse, and apply strict CORS policies only when browser-based clients need access; otherwise, prefer default-deny postures.

For dependency and environment management, `uv` offers a fast resolver, reproducible lockfiles, and per-project isolation aligned with `pyproject.toml`. Treat version pinning as an operational control, maintain a `constraints.txt` for critical libraries such as Temporal, FastAPI, Pydantic, and httpx, and consider separate lockfiles for dev, staging, and production to accommodate differences in reproducibility and performance requirements.

Suggested uv workflow
```bash
# create and activate an environment
uv venv .venv && source .venv/bin/activate

# initialize pyproject and add deps
uv init
uv add fastapi uvicorn httpx pydantic pydantic-ai temporalio logfire

# lock and export if needed for CI
uv lock
uv export --format requirements-txt > requirements.txt

# run the app
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

ASGI servers: Uvicorn vs Hypercorn
- Uvicorn: high-performance ASGI server using `uvloop` and `httptools`; supports HTTP/1.1, WebSockets, HTTP/2 (h11/h2 backends). Simple to operate and widely used with FastAPI.
- Hypercorn: flexible ASGI server supporting HTTP/1.1, HTTP/2, HTTP/3 (QUIC) and multiple concurrency backends (`asyncio`, `uvloop`, `trio`). Good fit when HTTP/2/3 or Trio is required.

Operational guidance
- Benchmark both under representative load (concurrency, payload sizes, keep-alives). Choose based on protocol needs and latency tail behavior.
- For Uvicorn, common production setup is `gunicorn -k uvicorn.workers.UvicornWorker -w <N> app.main:app` with `<N>` sized to cores.
- For Hypercorn, run `hypercorn --workers <N> --bind 0.0.0.0:8000 app.main:app` and enable HTTP/3 if needed with proper TLS/ALPN.

Example Hypercorn config (toml)
```toml
bind = ["0.0.0.0:8000"]
workers = 4
keep_alive_timeout = 5
graceful_timeout = 15
alpn_protocols = ["h2", "h3", "http/1.1"]
quic_bind = ["0.0.0.0:443"]
```


## Infrastructure: Railway

Railway’s promise is speed-to-value with pragmatic controls. For this architecture, that means you can get an API, an orchestrator, and an agent service online in minutes, yet still enforce separation of concerns and robust secret management. The golden path is a multi-service project, one per process type, each with its own CPU/memory profile, env vars, health checks, and scaling rules. Keep services stateless and push state into managed offerings: Supabase Postgres for relational and vectors, Logfire for observability, and Temporal (self-managed or remote) for orchestration. Use Railway environments (dev, preview, prod) to encode promotion workflows: PRs auto-deploy to preview with synthetic webhooks disabled; staging mirrors production traffic patterns with feature flags on; prod receives only signed images and migrations that have passed load tests. Document the exact steps to recover from a failed deploy, including how to roll back schema changes and drain message adapters.

Principles
Structure a multi-service project in Railway so that each process type—API, orchestrator, agent, vector database, relational database—has its own lifecycle, resources, and scaling rules. Codify provisioning with templates or a `railway.json` manifest so environments can be recreated consistently. Keep secrets and operational variables in Railway’s environment store rather than source control, separating dev, staging, and production to avoid accidental cross-contamination. Persist state in managed offerings wherever possible: use Railway-managed Postgres for relational data, pair it with a managed vector store when available or a containerized vector database with attached volumes when necessary, and keep stateless services easy to roll.

Recommended service split
An API service implements FastAPI webhooks and admin endpoints and should run at two or three replicas with health checks for graceful rollouts. An orchestrator service hosts Temporal workers that execute workflows and activities and scales horizontally by task queue. An agent service runs the Pydantic AI runtime and its tools; you can co‑locate this with the orchestrator for simplicity or separate it for isolation and resource specialization. For scheduled work, use Railway’s cron or deploy hooks to invoke admin endpoints that enqueue jobs, though Temporal Schedules are preferred for durability and observability. Finally, centralize observability by exporting Logfire and OpenTelemetry data and shipping application logs to Railway’s logging or an external sink.

Deployment notes
Prefer a Dockerfile for deterministic builds that pin Python and the base OS and use multi-stage builds to keep images small. Configure process-level settings such as `UVICORN_WORKERS`, log verbosity, and memory limits explicitly rather than relying on defaults. Run database migrations as part of the deploy pipeline either via a dedicated hook or a one-off job to keep schema changes synchronized with code. Enable pull-request deploys to create ephemeral preview environments, but disable outbound callbacks to production vendors for safety. Control spend by setting concurrency limits and autoscaling rules per service so that load spikes do not produce runaway costs.


## Database: Supabase (Postgres + pgvector)

Rationale
Supabase provides a unified operational envelope by combining managed Postgres for relational data with pgvector for embeddings, reducing the need to operate separate data systems for truth and semantics. Its developer experience includes first-class authentication, Row Level Security that enables per-tenant or per-user isolation at the database layer, built-in object storage, and support for functions and triggers, along with observability and automated backups that simplify life-cycle management.

Designing the data layer for a conversational agent is a balancing act between relational truth and vector semantics. Supabase gives you both in one operational envelope, which simplifies backups, access control, and cost visibility. Use relational tables for the canonical source of truth—users, conversations, messages metadata, consents, and introduction transactions—and use pgvector to accelerate semantic retrieval for memory and recommendations. Keep embeddings small and purposeful: store embeddings for summaries and profile cards rather than every token of every message. Summaries change infrequently and carry far more signal for downstream retrieval than raw, verbose transcripts. Pair that with metadata indexes (user_id, topic, created_at) to support hybrid search: filter by who and when, then rank by vector similarity.

Schema guidance
Model tables such as `users`, `conversations`, `messages`, `profiles`, `intros`, event ledgers for EDA, an `embeddings` table for pgvector, and `consents` for auditable permissioning. Use stable `user_id` keys that span channels and add composite indexes like `(channel, conversation_id)` to accelerate hot paths, with partial indexes for unread or recent items. For vectors, choose a dimension appropriate for your embedding model—for example `vector(1536)`—and store ancillary attributes in `jsonb` metadata. Select HNSW or IVFFlat indexes based on your corpus size and query patterns, balancing recall and latency.

RLS and security
Adopt a default-deny posture and write explicit Row Level Security policies that scope access by tenant or user, using a service role key only for trusted server processes. Avoid storing raw message bodies when you can; prefer redacted records and keep attachments in a secure object store with signed URLs so that access can be audited and revoked.

Functions and triggers
Use triggers on ingestion to update `embeddings` when new summarized notes are written, and maintain an outbox table paired with triggers to enqueue reliable sends to a worker or message bus. This ensures side effects can be retried without duplicating downstream actions.

Operations
Schedule backups with point‑in‑time recovery and practice restores on a regular cadence so recovery procedures are fresh and verified. Manage schema evolution with Alembic or SQL migrations executed in CI before deployment to catch conflicts early. Monitor slow queries and index bloat, and run `VACUUM` as needed to maintain predictable performance.

## Advanced Topics

### Long-term conversational design

Memory taxonomy
Working memory is the short-lived conversation window that maintains immediate coherence within an interaction, and it should be treated as expendable context rather than a durable store. Episodic memory captures durable summaries of past interactions with timestamps, sentiment, and intent annotations so the system can answer “what happened when” and prime future reasoning. Semantic memory stores facts about the user, including stable preferences, goals, entities, and relationships; it is the substrate for retrieval and recommendations and therefore must be validated, deduplicated, and versioned. Procedural memory encodes the how‑tos and policies that govern agent behavior—the steps it follows, the constraints it must honor, and the escalation rules—so changes can be reviewed like code and rolled out safely.

Techniques
Progressive summarization converts verbose exchanges into compact, high‑signal artifacts after a configurable number of turns, feeding semantic memory with updates while preserving the raw transcript elsewhere for audit. Time‑decay and pinning balance recall and privacy by allowing low‑value memories to fade while keeping critical facts—consents, commitments, and stable preferences—pinned with explicit lifetimes and renewal logic. When brokering introductions, double opt‑in is mandatory: the system must obtain consent from both parties and include contextual summaries and safety tips before connecting them. Event relevance should combine geo and time filters with embeddings so that suggested activities align with the user’s locale, schedule, and interests, surfacing a small, high‑quality set instead of an indiscriminate feed. Throughout, maintain a consistent persona with adjustable style knobs—formality, enthusiasm, brevity—so tone varies per user without drifting off brand.

Safety and ethics
Safety spans content moderation for both inputs and outputs, with escalation paths to human reviewers on edge cases, and a commitment to avoid over‑claiming capabilities: the agent must be transparent when uncertain and clearly describe limitations. Fairness requires monitoring recommendation diversity and preventing echo chambers, especially in introductions and event suggestions where over‑personalization can reduce opportunity and trust.


The cognitive architecture of a production agent should be explicit. Treat the memory taxonomy (working, episodic, semantic, procedural) as a contract with storage and retrieval behavior suited to each tier:
- Working memory is an in-process sliding window optimized for immediate coherence and short-term grounding; it should be cheap to construct and discard, and never used as a durable store.
- Episodic memory captures durable summaries of interactions with time, sentiment, and intent annotations; it enables “what happened when” questions and supports periodic compression.
- Semantic memory stores user facts, preferences, entities, and relationships; it is the substrate for recommendations and introductions and must be validated, deduplicated, and versioned.
- Procedural memory encodes policies and playbooks for agent behavior—what the agent is allowed to do and how; changes here should be reviewed like code and rolled out behind flags.

Retention and forgetting strategies are first-class. Progressive summarization should be deterministic and auditable: define templates for what gets retained (facts, decisions, commitments), what decays (low-signal chit-chat), and what must never persist (sensitive secrets). Summaries should carry provenance (message ids, timestamps, sources) and confidence, with a path to regenerate from raw transcripts when policies change. Couple time-decay with event-driven pinning: important user facts or commitments (consents, scheduled intros) should be pinned with explicit TTLs and renewal logic. As your system scales, add lifecycle hooks to move stale episodic memories to colder tiers and to periodically reevaluate semantic memories for drift.

Introduce typed memory tools for the agent rather than exposing raw storage. Examples: `retrieve_user_profile(user_id) -> UserProfile`, `retrieve_events(query: EventsQuery) -> list[Event]`, `upsert_memory(update: MemoryUpdate) -> MemoryAck`. When these tools are delivered via MCP, they become portable and discoverable across services and languages, and can be secured with per-tool scopes. Pair tool governance with evaluation datasets that score recall, precision, and the incidence of policy violations. Finally, align the agent persona with memory behavior: a concise persona should prefer brief summaries and direct prompts, while a reflective persona might capture rationales and hypotheses in episodic memory for later critique.


### Context engineering

RAG pipeline design benefits from deliberate decisions at each stage. During ingestion, adopt chunking strategies that reflect the structure of your sources, whether semantic segmentation or separator‑based splits, and attach metadata such as time, source, and user identifiers to support filtered search. In the indexing stage, choose a vector database that supports metadata filters and consider diversity‑promoting techniques like Maximal Marginal Relevance or lightweight re‑ranking so top‑K results are both relevant and non‑redundant. For query planning, classify intent—answer a question, recommend content, introduce people, or retrieve policy—and construct retrieval queries that align with that intent instead of using a one‑size‑fits‑all approach. Finally, enforce grounding and citation habits by including source titles and links with every snippet and allowing the agent to quote relevant passages verbatim where fidelity matters.

Memory compression turns verbose transcripts into durable, high‑signal artifacts. Use periodic summarization with explicit templates that specify what to retain—facts, decisions, commitments—and maintain a rolling “profile card” per user that captures stable preferences and recent changes. Store embeddings of these summaries to enable fast semantic recall without re‑ingesting entire transcripts.

Evaluation must happen offline and online. Offline, test information recall, track hallucination rates, and score citation accuracy so you know whether the system grounds answers in the right sources. Online, measure customer satisfaction, resolution rates, introduction acceptance, retention, and message latency; these live metrics tell you whether improvements on paper translate into user value.


Build context as a product, not an afterthought. A robust pipeline starts with intent classification (answer, plan, retrieve policy, recommend, introduce), proceeds to a retrieval plan that enumerates which memories and sources to consult, and ends with a bounded, well-cited context package. Within retrieval, combine hybrid search (metadata filters + vector similarity) with diversity-promoting techniques (MMR or re-ranking) to avoid tunnel vision. When sources are heterogeneous (transcripts, profile cards, events, docs), normalize into a common snippet schema with fields for `title`, `body`, `source`, `last_updated`, and `attribution` so downstream prompts can treat them uniformly.

Guardrails should be enforced via tool schemas and policy prompts that reference those schemas. For example, a `retrieve_events` tool can enforce geographic and temporal filters server-side, ensuring the agent cannot request disallowed scopes. At the prompt layer, encode explicit citation requirements: whenever a claim is grounded in retrieved context, include source titles and anchors and prefer verbatim quotes for critical facts. Evaluate context construction separately from final answers using offline suites: recall@K for relevant facts, citation accuracy, and leakage (presence of disallowed content). A well-designed context system also clarifies what not to include: avoid stuffing the entire transcript or redundant snippets, and prefer concise, high-signal summaries with clear delimiters.

Finally, treat context size and latency as budgets to be spent deliberately. Track token and time budgets per request; when over budget, degrade gracefully by pruning low-utility snippets first (e.g., oldest, lowest confidence). For streaming agents, stage retrieval: begin with high-confidence, low-latency sources, then progressively refine with slower or more expensive lookups if the user stays engaged. Expose context provenance in observability so that operators can debug failures (e.g., missing citations) and tune retrieval plans without altering agent prompts.


### DSPy for prompt and workflow optimization

Why DSPy
DSPy brings programmatic rigor to prompt and workflow engineering by formalizing tasks as typed signatures with teleprompters that can be optimized against datasets. Because signatures define inputs and outputs, the framework naturally supports structured results that align with Pydantic models, reducing prompt drift and making both offline and online optimization reproducible.

DSPy encourages you to think about prompts the way you think about code: there is a signature with explicit inputs and outputs, a set of examples with ground-truth labels, and an optimizer that can search the space of phrasing, demonstrations, and tool-call constraints. For our agent, this means we can define an “introduction message” signature with required fields, measure success by human ratings and downstream acceptance, and let DSPy discover phrasing that consistently steers the model to structured, on-brand outputs. Offline, we run optimization jobs against historical datasets; online, we roll out the winning variants to a small percentage of traffic, measure engagement, and promote or rollback based on SLOs.

Offline optimization
Begin with curated few‑shot traces and explicit evaluation metrics—accuracy, factuality, and style—so that you can tune prompts and tools with clear targets. Store variants and their metrics in Supabase and choose the best candidate per task type with a transparent record of improvement and trade‑offs.

Online adaptation
Move candidates into production behind flags and A/B test them on key tasks such as introductions and event suggestions. Capture quality ratings, follow‑through, and downstream outcomes to refine prompts periodically and retire underperforming variants.

Example (sketch)
```python
# Define a signature for an intro message generator with constraints
class IntroSignature:
    input_fields = ["seeker_profile", "candidate_profile", "topic"]
    output_fields = ["message_to_a", "message_to_b", "tone"]

# DSPy teleprompter config and evaluation hooks would go here
```


Operationalize prompt engineering like any other optimization problem. With DSPy, you express tasks as signatures (typed inputs and outputs) and let optimizers search over prompt phrasing, examples, and tool-call constraints. Start by curating small, high-quality datasets with ground truth labels aligned to product outcomes (e.g., “intro message helpfulness” scored by humans). Use the datasets to tune teleprompters offline, recording not just aggregate metrics but per-example deltas to identify regressions in corner cases. Persist winning variants with semantic versioning and human-readable change logs so that rollbacks are safe and auditable.

In production, deploy variants behind flags and use online experiments to validate gains. Choose metrics that reflect user value and system health: response helpfulness or CSAT, introduction acceptance rate, message latency, and tool-call error rates. Keep a strict budget for LLM tokens and tool invocations; an “improved” prompt that doubles cost under load is a regression. Pair A/B tests with guardrails: rate-limit new variants, add canaries to high-risk cohorts, and automatically rollback on error spikes. Periodically retrain or re-optimize to counter drift—tool schemas, memory distributions, and channel behaviors change over time—and bake this cadence into your release calendar.

Finally, align DSPy work with typed interfaces. If a tool output expands (e.g., adding a `confidence` field), include it in the signature and update evaluation suites accordingly. When a variant performs differently across segments (e.g., terse vs verbose personas), split signatures or include segment features so the optimizer can discover stable policies rather than overfitting to the global average. The north star is reproducibility: given the same signature, seed, and dataset, the optimizer should converge to a documented variant that your team can reason about.


### Vector search and embeddings-based recommendations

Design choices
Embedding selection should match the semantic granularity of your content and tasks; short summaries and profile cards benefit from models tuned to concise texts, while long documents may call for models with stronger context handling or domain-specific finetuning. Indexing strategy follows scale and latency goals: HNSW indexes often offer strong recall‑latency trade‑offs at moderate scale, while IVF or product quantization variants help at very large cardinalities. Hybrid search—combining lexical scoring such as BM25 with semantic vectors and then re‑ranking the top‑K—typically yields more robust results than either approach alone. To keep recommendations timely, store timestamps with items and boost recency explicitly for events and opportunities that have a shelf life.

Matching and intros
For introductions, model the problem as a user–interest bipartite graph augmented with vector similarity so that semantic closeness influences candidate selection without overwhelming structural signals. Apply multi‑objective ranking to balance relevance with diversity and novelty, and encode explicit fairness constraints to prevent homogenization. Close the loop with feedback: capture thumbs‑up or thumbs‑down and measure follow‑through signals such as replies and RSVPs so that bandit algorithms or lightweight reinforcement learning can personalize over time.

Metrics
Evaluation needs an offline and online face. Offline, track ranking quality with metrics like NDCG@K and MRR, and watch coverage and diversity to ensure the system does not collapse onto a narrow set of items. Online, measure conversion to conversation, introduction acceptance rate, and RSVP rates; these operational metrics tell you whether improved ranking translates into real user value.


Treat vector search as a system with tunable levers, not a black box. Choose embedding models based on the semantic granularity you need (short summaries vs long documents) and the languages and domains you serve. Keep dimensionality and index types pragmatic: HNSW often provides a strong default for recall/latency trade-offs at moderate scale, while IVF or PQ variants become attractive at very large cardinalities. Always pair vectors with rich metadata filters—geo, skills, recency—to form the first-stage candidate set, and then re-rank with a lightweight lexical or cross-encoder model when quality demands it.

Cold-start and fairness are product requirements, not afterthoughts. For new users, bootstrap with profile priors, popular items, or exploration-heavy bandits; set explicit diversity constraints to prevent echo chambers. For introductions, enforce multi-objective ranking that balances semantic closeness with diversity and novelty, and include guardrails to avoid sensitive pairings. Instrument feedback loops: capture explicit ratings (thumbs up/down), implicit signals (reply latency, link clicks), and outcomes (intro acceptance), and feed these into periodic retraining or weight updates. Keep evaluations honest with temporally-split datasets to avoid leakage from future data.

On the operational side, track index health and cost. Measure build and refresh times, memory footprint, and query latency distributions. Implement canaries for index changes and maintain a safe rollback path to a previous index snapshot. For privacy, avoid storing raw message bodies as vector text; prefer compact summaries and enforce retention policies. When recommendations must explain themselves, store short rationales alongside candidates (e.g., “both mentioned data visualization in the past month”) and surface them in the UI to build trust.


### Event-driven architecture (EDA)

Principles
EDA favors loose coupling by treating events as the lingua franca of the platform; services consume the subsets they need without central orchestration coupling them tightly. To counter the reality that delivery is at‑least‑once, idempotency and deduplication must be built in, typically with event identifiers and the outbox pattern so state changes and dispatch are committed atomically. Backpressure handling is critical: consumers should apply bounded concurrency and expose dead‑letter queues so poison messages can be isolated, and the system should support replays for recovery and investigative audits.

Patterns
The outbox/inbox pair is the cornerstone of reliable eventing because it preserves a durable record of intent and allows retry without duplication when paired with idempotent consumers. A schema registry turns events into versioned contracts; evolve them additively first, and when breaking changes are unavoidable, run old and new versions side by side during migration. Exactly‑once semantics are unattainable at scale, so design consumers to be idempotent and observability to highlight when retries occur. Always correlate events with trace context and conversation identifiers so you can stitch cross‑service narratives during incidents and analyses.

Temporal + EDA
Temporal complements EDA by holding long‑lived state and retries within workflows while events remain the medium of communication between services. Webhook handlers publish events that signal running ConversationWorkflow instances, which own timers and state transitions durably. Conversely, workflows emit events for downstream analytics and notifications so that external systems remain decoupled from workflow internals while still responding to state changes in near‑real time.


Design events as durable, versioned contracts. Adopt an additive-first evolution policy (new fields are optional, defaults are explicit) and reserve breaking changes for major versions with side-by-side consumers. Every event should carry correlation identifiers (request id, conversation id, workflow id) and trace context so that observability can stitch cross-service causality. Validate events at the boundary with JSON Schema, reject invalid payloads early, and route failures to dead-letter queues with clear operator guidance for replays or drops.

Temporal complements EDA by owning long-lived state and retries while events remain the lingua franca between services. Keep non-determinism out of workflows; activities perform side effects with idempotency keys and exponential backoff. Signals connect inbound events (e.g., a message from Twilio) to the correct workflow instance, while queries expose introspection for dashboards and support tooling. For schedules, prefer Temporal Schedules over external cron so retries, jitter, and observability live in one place. Document operational playbooks: how to drain a failing adapter, how to pause/resume cohorts, how to roll back a schema change without losing messages.

Finally, layer resilience patterns systematically: outbox/inbox tables for exactly-once-like behavior, circuit breakers and bulkheads to contain provider outages, and backpressure-aware consumers that scale horizontally under load. Use cost-aware routing when multiple providers can fulfill an action (e.g., WhatsApp vs SMS fallback) and persist decision rationale in events for auditability. The outcome is a platform where change is routine and incidents are bounded by design, not by luck.


## Types and type safety (first-class)

A type-first approach is more than aesthetics; it is a risk mitigation strategy for systems that must evolve continuously while handling sensitive, user-generated content. Normalization does not mean flattening away information—rather, it means creating a stable, minimal domain shape for downstream logic and preserving rich vendor details alongside it. This split lets workflows and agents operate on a simple API that is consistent across channels, while adapters maintain fidelity to vendor specifics for auditing and advanced features. Over time, this choice pays compounding dividends: tests get simpler, features ship faster because they touch fewer components, and incidents are easier to diagnose because you can diff a small set of domain events instead of piles of vendor payloads.

Why type-first
A type-first approach makes determinism and safety table stakes for Temporal workflows, activities, and signals/queries, because explicit types constrain what can happen at the edges and make replays predictable. Pydantic AI tools benefit from precise input and output schemas, which turn tool invocation into a validated contract rather than a suggestive prompt. Normalizing messages from LoopMessage, Twilio, and WhatsApp into strongly typed domain events unifies processing and reduces the chance of leaky abstractions, while preserving vendor-specific details alongside for audit and advanced features.

Type normalization layer
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, Optional

Channel = Literal["imessage", "sms", "whatsapp"]

class InboundMessage(BaseModel):
    id: str
    channel: Channel
    conversation_id: str
    from_user_id: str
    to_user_id: Optional[str] = None
    text: Optional[str] = None
    media: list[HttpUrl] = []
    raw_vendor: dict = Field(default_factory=dict)

class OutboundMessage(BaseModel):
    idempotency_key: str
    channel: Channel
    to_user_id: str
    text: Optional[str] = None
    media: list[HttpUrl] = []
```

Typed Temporal interfaces
```python
from temporalio import workflow
from pydantic import BaseModel

class SignalInbound(BaseModel):
    message: InboundMessage

@workflow.defn
class ConversationWorkflow:
    @workflow.run
    async def run(self, user_id: str):
        ...

    @workflow.signal
    async def inbound(self, payload: SignalInbound):
        ...

    @workflow.query
    def profile_summary(self) -> dict:
        ...
```

Typed Pydantic AI tools
```python
from pydantic import BaseModel

class RecommendIntroInput(BaseModel):
    seeker_user_id: str
    max_candidates: int = 5

class Candidate(BaseModel):
    user_id: str
    reason: str

class RecommendIntroOutput(BaseModel):
    candidates: list[Candidate]
```

Vendor DTOs and adapters
Keep vendor‑specific DTOs such as `LoopMessageWebhook`, `TwilioSMSWebhook`, and `WhatsAppWebhook` confined to adapter modules so that the rest of the codebase does not become entangled with provider schemas. At the boundary, convert these payloads to unified domain types like `InboundMessage` and include vendor fields in a `raw_vendor` envelope for auditing and advanced features that do not fit the unified abstraction cleanly.

Typed vendor event examples
```python
class TwilioSMSWebhook(BaseModel):
    From: str
    To: str
    Body: str | None = None
    MessageSid: str
    NumMedia: int = 0

class WhatsAppWebhook(BaseModel):
    wa_id: str
    phone_number_id: str
    message_id: str
    text: str | None = None

class NormalizationPrinciples(BaseModel):
    # document choices for unified schema
    rationale: str
    pros: list[str]
    cons: list[str]
```

Normalization pros
Unifying event shapes simplifies processing and storage across services and leads to cleaner analytics and Temporal signals. It also makes testing and replay dramatically easier because golden traces and fixtures only need to cover a single, stable shape.

Normalization cons
There is always a risk of losing channel-specific nuance if details are not preserved in a `raw_vendor` field, and leaky abstractions can appear when features diverge substantially across providers, such as reactions or threading models that do not map perfectly to the unified schema. Counteract these risks by documenting design choices and versioning the unified contract as new features emerge.


## Software engineering patterns

Patterns are the scaffolding that keep complex systems from collapsing under their own weight. Messaging platforms evolve, SDKs deprecate, providers change rate limits, and policies shift. The antidote is to isolate variability behind ports and adapters, to choose strategies dynamically based on typed context, and to ensure that recovery logic (outbox, retries, circuit breakers) is systematic rather than ad hoc. This section augments the earlier interface definitions with concrete usage guidance so your team can share a common mental model and avoid re-inventing error handling at every call site.

Goals
The patterns in this section aim to encapsulate vendor differences—across LoopMessage, Twilio, and WhatsApp—behind a stable interface so that business logic is insulated from SDK churn and provider quirks. They promote dependency injection to make components testable in isolation using fakes and fixtures, and they support runtime routing so per-user channel preferences and consent policies can be enacted without invasive changes as SDKs and capabilities evolve.

Core interfaces (Ports and Adapters)
```python
from abc import ABC, abstractmethod

class MessagingPort(ABC):
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> str: ...

    @abstractmethod
    async def parse_inbound(self, raw: dict) -> InboundMessage: ...
```

Adapters
```python
class LoopMessageAdapter(MessagingPort):
    async def send(self, msg: OutboundMessage) -> str:
        # call LoopMessage API
        ...
    async def parse_inbound(self, raw: dict) -> InboundMessage:
        # map LoopMessageWebhook -> InboundMessage
        ...

class TwilioAdapter(MessagingPort):
    async def send(self, msg: OutboundMessage) -> str: ...
    async def parse_inbound(self, raw: dict) -> InboundMessage: ...

class WhatsAppAdapter(MessagingPort):
    async def send(self, msg: OutboundMessage) -> str: ...
    async def parse_inbound(self, raw: dict) -> InboundMessage: ...
```

Adapter registry and DI
```python
from typing import Dict

class MessagingRegistry:
    def __init__(self, adapters: Dict[Channel, MessagingPort]):
        self.adapters = adapters

    def get(self, channel: Channel) -> MessagingPort:
        return self.adapters[channel]

registry = MessagingRegistry({
    "imessage": LoopMessageAdapter(),
    "sms": TwilioAdapter(),
    "whatsapp": WhatsAppAdapter(),
})

# In FastAPI, inject via dependencies
```

Evolution and versioning
Adaptability comes from confining change to the edges. Use feature flags and adapter configuration to enable or disable capabilities per channel at runtime, and introduce new adapters without touching core business logic. Maintain contract tests for each adapter—covering both inbound parsing and outbound send behavior—using vendor sample payloads to guard against regressions when providers update schemas.

Additional patterns and applications
Employ a strategy pattern for channel selection so that the system can decide at runtime which channel to use for a given user and context based on cost, reliability, and consent, with clean fallback logic. Add circuit breakers and bulkheads to prevent failures in one provider from cascading across the system and cap concurrency on a per-adapter basis to avoid resource starvation. Implement the outbox pattern so message writes and send intents are committed atomically, with an asynchronous dispatcher ensuring at‑least‑once delivery under failure. Pair retries with exponential backoff and idempotency keys to make re-sends safe across flaky networks. For user-facing content, use a builder pattern to assemble prompt and message variants deterministically under constraints, and apply the specification pattern to compose filters for candidate retrieval and ranking when recommending introductions.

Putting it together
In practice, a new “send-introduction” feature means adding a new tool with typed inputs/outputs, extending the orchestrator workflow to call that tool, and relying on the messaging registry to deliver the final messages over the preferred channel. If Twilio throttles or WhatsApp templates fail, the circuit breaker trips and the outbox retry picks up later; the workflow doesn’t duplicate work because idempotency keys protect side effects. When LoopMessage introduces a new reaction event, only the adapter changes to map that payload to `InboundMessage` with a `raw_vendor` field for the reaction detail. Business logic remains clean, testable, and boring—the compliment you want for systems at scale.


## Security

Security is the property that the system resists unauthorized access, misuse, and data exfiltration under realistic adversarial pressure. It must be engineered from the outset—“secure by design”—and sustained through implementation, deployment, and ongoing operations.

Threat modeling and trust boundaries
Start by enumerating actors such as end users, operators, MCP servers, and third‑party APIs, and assets such as PII, credentials, embeddings, transcripts, and consents. Draw data flows, mark trust boundaries—public webhooks, provider callbacks, MCP connections, and database access—and apply a framework like STRIDE to identify threats. Translate the mitigations into concrete acceptance criteria so that security posture is testable and non‑negotiable.

Access control and identity
Apply least privilege everywhere, separating human and machine identities and using short‑lived credentials and scoped tokens. Where possible, adopt workload identity to avoid static secrets. Protect admin endpoints and dashboards with role‑based access control, and gate destructive actions behind break‑glass procedures with audit trails.

Secrets management
Keep secrets in a vault, not in source control or plaintext environment files. Rotate keys routinely and after incidents, and use hardware‑backed keys when feasible. Ensure MCP connections and provider SDKs read credentials from secure stores with granular scopes to minimize blast radius.

Data protection and minimization
Collect only what is necessary to deliver value. Encrypt data in transit using modern TLS and at rest at disk or field level where appropriate. Tokenize or hash identifiers in logs, store redacted versions of transcripts by default, and require explicit, time‑limited justifications for access to raw content.

Secure coding and dependencies
Validate and sanitize all inputs at boundaries, including webhooks, admin APIs, and MCP tool results. Avoid dynamic evaluation, pin dependencies, and scan regularly with SAST and software composition analysis. Prefer memory‑safe patterns and parameterized queries, and centralize HTTP clients with strict defaults for timeouts, retries, and certificate handling.

Security testing and verification
Combine SAST for code with DAST against running systems, add fuzzing to webhook parsers and adapters, and schedule regular penetration tests. Instrument anomaly detection for unusual traffic and authentication patterns, and maintain an incident response runbook that defines roles, communications, and evidence collection so you can execute under pressure.

Examples and tips
At the edge, validate Twilio signatures and WhatsApp verification tokens and reject failures with 403. For MCP, validate server certificates and tool schemas and deny unknown tools by default. In storage, separate the hot operational path from the cold content path and apply distinct controls and encryption keys to reduce cross‑contamination risk.


## Compliance

Compliance aligns system behavior with laws, regulations, and contractual obligations, reducing legal and operational risk while building user trust. The work begins with clear scope: map your data flows to applicable regimes—GDPR for EU data subjects, CCPA/CPRA in California, HIPAA if you touch protected health information, PCI DSS if you process cards—and document what applies, what does not, and why. Messaging brings its own platform‑specific rules: A2P 10DLC registration in the U.S. and WhatsApp’s template policies must be encoded as system behavior rather than tribal knowledge.

Support data subject rights by providing mechanisms to export, correct, and delete user data. Track provenance and retention lifecycles not only for raw transcripts but also for summaries, embeddings, and consents. Maintain a Record of Processing Activities and a data inventory that maps fields to systems and owners, and enforce Row Level Security with default‑deny policies so access is explicit rather than implied. Enforce policy in code: STOP and HELP flows should function reliably for SMS, WhatsApp’s 24‑hour customer care window and template categories must be honored, consents should be logged with timestamps and scope, and processing should be denied when allowed bases are missing, with operator‑facing explanations that make decisions transparent.

Auditing and attestations require immutable logs for admin access, schema changes, and sensitive data reads. Schedule internal audits and engage third parties for periodic assessments, tracking findings to remediation with owners and deadlines. Version your compliance policies and link them to CI checks and deploy gates so violations block release rather than surfacing after the fact. Encrypt thoughtfully with distinct keys per environment and per data class; rotate keys routinely; and enforce TLS everywhere, including service‑to‑service and MCP transports. Consider envelope encryption for highly sensitive payloads and field‑level encryption for PII hotspots.

Finally, invest in training and awareness. Run onboarding and annual refreshers covering the secure handling of PII, phishing risks, and incident response. Provide specialized playbooks for on‑call engineers and data handlers, and test readiness with tabletop exercises. For feasibility, begin with a minimal viable program aligned to your risk surface: codify required messaging rules, build DSAR pipelines, and implement structured retention, then layer in formal frameworks as the product and data surface grow.


## Testing

Testing provides empirical evidence that the system meets its functional and nonfunctional requirements under realistic conditions.

Unit and contract testing verify the smallest units and the external contracts at your boundaries. Cover tool functions—including those proxied through MCP—with deterministic tests that exercise happy and unhappy paths. For webhooks and provider callbacks, write contract tests that validate exact payload parsing and signature verification, such as Twilio’s `X-Twilio-Signature` and WhatsApp’s verification flow, and assert both acceptance and rejection behavior so regressions do not silently weaken your posture.

Integration and end-to-end testing exercise the full flow from the FastAPI ingress through the orchestrator, into the agent and adapters, and back out to providers. Use golden transcripts and seeded data to make reasoning and tool selection deterministic and include failure modes—timeouts, HTTP 429 throttling, invalid WhatsApp templates—to validate that retries and idempotency keys produce safe, observable behavior under stress.

Performance and scalability testing targets both hot endpoints and long‑running workflows. Load test webhook routes and Temporal workers with realistic payloads and arrival patterns and measure p50/p95/p99 latencies, throughput, and error rates. Identify saturation points—thread pools, database connections, vector index queries per second—and configure autoscaling and circuit breakers so the system degrades gracefully instead of falling over.

Security and resilience testing complement functional checks. Integrate SAST and DAST into CI, fuzz webhook parsers and adapter boundaries, and schedule chaos experiments that simulate provider outages, MCP latency spikes, and database failovers. During these drills, confirm that fallbacks—such as SMS in response to iMessage or WhatsApp issues—activate safely and that users receive clear, transparent explanations.

Regression and change management ensure upgrades do not erode quality. Guard against behavioral drift with snapshot tests of prompts and tool outputs backed by dataset‑driven suites. Use canary deployments for agent and workflow updates, watch key error and latency signals, and roll back automatically if thresholds are breached.

Pragmatically, integrate tests into CI as fast, parallelizable jobs. Provide developer harnesses that replay recorded webhooks and provider responses locally so engineers can iterate without vendor dependencies. When working with partners, export minimal fixtures that match vendor expectations to accelerate certification.


## Reliability

Reliability is the probability that the system performs as intended over time, and it is achieved through redundancy, isolation, observability, and disciplined change management. Architecturally, isolate failure domains with bulkheads—per‑adapter thread pools and rate limits—and apply provider‑specific circuit breakers so that a single vendor outage does not cascade. Use outbox/inbox tables for durable messaging and idempotency keys for side effects so retries do not duplicate work, and prefer Temporal for long‑lived orchestration where retries and timers are first‑class and observable.

Capacity planning and scaling must be proactive. Right‑size worker pools and database connections, set per‑queue concurrency caps, and autoscale on leading indicators such as queue depth and latency with sensible floors and ceilings to prevent thrash. Treat agent tokens and tool invocations as budgets to prevent cost‑induced instability during spikes.

Observability and SLOs translate engineering choices into operational guarantees. Define SLOs for webhook latency, workflow success, tool call success rates, and message delivery by channel, and instrument with Logfire and OpenTelemetry while propagating correlation identifiers end‑to‑end. Alert on SLO burn rates and budget consumption rather than raw error counts so responders focus on user impact.

Change and incident management keep reliability intact during evolution. Use feature flags for risky capabilities and roll out gradually. Maintain runbooks for provider outages, MCP server degradation, and schema migrations, and practice disaster recovery regularly: restore from backups, drain adapters, and roll workers mid‑run to validate assumptions. After incidents, conduct postmortems that produce actionable prevention items and track their completion.

Cost and efficiency are reliability concerns. Track per‑feature and per‑tenant costs for LLM tokens, vector queries, and messaging; cache deterministic results where safe; and batch embeddings to smooth load. Prefer incremental index updates for vector stores and measure tail latencies because p99 behavior often determines perceived quality.

As a feasibility baseline, run two or more API replicas, keep separate task queues for workflows and activities, precompute idempotency keys before side effects, document user‑consented fallbacks such as iMessage‑to‑SMS, and schedule periodic game days to validate that your reliability narrative holds under stress.



## Production-grade software considerations

Code health & maintainability
Treat formatting, type checks, and documentation as guardrails that keep velocity high without sacrificing correctness. Automate ruff/black to keep diffs small and focus code review on substance. Run mypy or pyright in CI to catch type errors before they ship, and aim for pragmatic docstring coverage so complex functions and modules are self-explanatory. Maintain strong modular boundaries using ports-and-adapters: vendor SDKs and provider-specific logic live in adapters, while workflows and agents contain durable business logic with typed interfaces.

Reliability engineering: Craft explicit SLOs for API latency (p95, p99), workflow step success, and message delivery success by channel. Build error budgets and make them visible so product and engineering share a common language for launch risk. 

Practice disaster recovery: intentionally fail adapters, revoke credentials, and roll a Temporal worker deployment mid-run to verify that durable execution and fallbacks behave as designed. When incidents happen, run postmortems that capture detection, diagnosis, and prevention actions; encode the latter into runbooks and automated checks. Finally, cost is a reliability concern: if a vendor bill explodes, throttling can create user-visible failures. Track per-feature and per-tenant costs for LLM calls, vector queries, and messaging so you can enforce budgets and optimize hot spots.

Business requirement variability
Expect requirements to change and make those changes cheap. Feature flags and configuration-driven behavior allow prompts, channels, and cadences to evolve without redeploying core services. Favor additive schema evolution and versioned APIs so clients can upgrade on their own schedule and in-flight workflows remain compatible.

Documentation & DX
Capture trade-offs in architecture decision records so future engineers understand why choices were made. Keep clear runbooks for incidents and concise onboarding guides to reduce time-to-productivity. For local development, standardize on `uv` environments seeded with representative data and mocked adapters so flows can be exercised without external dependencies.

Feasibility & reliability
Before launches, define SLOs for latency and error rates per endpoint and workflow and verify them with load tests that mirror expected traffic patterns. Run periodic game days to simulate critical fallback scenarios—such as iMessage relay downtime, WhatsApp template blocks, or carrier filtering—so the team can practice diagnosis and recovery with real telemetry.

Systematic considerations
Engineer the data lifecycle deliberately with defined retention, privacy reviews for new data fields, and tooling to export and delete user data on request. Build cost observability for LLM calls, messaging, and storage directly into dashboards so product decisions incorporate financial as well as technical constraints.


## Reference blueprints

Message flow (SMS example)
An inbound SMS from Twilio is received by the FastAPI webhook, which validates the provider signature and acknowledges quickly after enqueuing an internal event. That event becomes a Temporal signal to the user’s ConversationWorkflow instance, which evaluates context and decides whether to retrieve memory, plan next steps, or call a tool. The workflow invokes agent tools for recommendations or memory updates as needed, then schedules an activity to send the SMS reply with an idempotency key so retries won’t duplicate delivery. Throughout the flow, logs and traces are emitted to Logfire and your APM to maintain end‑to‑end visibility of latency, failures, and costs.

Service boundaries
The API gateway hosts FastAPI webhooks and admin APIs and serves as the typed, secure ingress to the platform. The orchestrator runs Temporal workers that own durable workflows and execute activities reliably. The agent process runs the Pydantic AI runtime and its tools and never speaks directly to the outside world, accepting strictly typed inputs and returning typed outputs. Memory is split between a vector database for semantic recall and a relational database for canonical truth and consent. Analytics consumes events via stream processing and writes to a warehouse for reporting, evaluation, and offline optimization.


## Curated references

- Twilio Programmable Messaging: https://www.twilio.com/docs/sms
- Twilio WhatsApp: https://www.twilio.com/docs/whatsapp
- Meta WhatsApp Business Cloud API: https://developers.facebook.com/docs/whatsapp
- LoopMessage docs: https://loopmessage.com and https://server.loopmessage.com (API)
- Pydantic Logfire docs: https://docs.pydantic.dev/logfire/ and https://logfire.pydantic.dev
- Temporal docs: https://docs.temporal.io
- FastAPI docs: https://fastapi.tiangolo.com
- Railway docs: https://docs.railway.app/
- Hypercorn docs: https://pgjones.gitlab.io/hypercorn/
- uv (Python package/deps manager): https://docs.astral.sh/uv/
- DSPy: https://dspy.ai/
- Supabase: https://supabase.com/docs




