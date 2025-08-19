# LoopMessage iMessage Conversation API — Mocking & Integration Test Spec

Sources:
- Webhooks/Callbacks: [LoopMessage docs](https://docs.loopmessage.com/imessage-conversation-api/webhooks)
- Sending Messages: [LoopMessage docs](https://docs.loopmessage.com/imessage-conversation-api/send-message)
- Statuses: [LoopMessage docs](https://docs.loopmessage.com/imessage-conversation-api/statuses)

## Purpose
This document enumerates endpoints, information flows, and JSON object shapes required to fully mock the LoopMessage iMessage Conversation API and build robust integration tests for conversation-driven scenarios.

## High-level Concepts
- **Outbound requests (our server → Loop)**: Send a message (text, audio, reaction) to an individual or a group.
- **Inbound webhooks (Loop → our server)**: Notifications for inbound messages and status updates for outbound messages.
- **Timing**: Our webhook handler must respond quickly (< 15s). Loop retries failed webhooks up to 30 times with backoff.
- **Authorization**: Outbound requests use headers; inbound webhooks can include an Authorization header we must verify.
- **Typing and Read acknowledgements**: We can optionally respond to specific webhooks with typing and read markers.

---

## Endpoints (Outbound → Loop)
Unless noted otherwise, these use the same base endpoint with different payload combinations.

- POST `/api/v1/message/send/`
  - Purpose: Send a message (text, audio, reaction) to a recipient or a group.
  - Headers:
    - `Authorization: <token>`
    - `Loop-Secret-Key: <secret>`
    - `Content-Type: application/json`
  - Request JSON (text message):
    - Required:
      - `text: string`
      - `sender_name: string` (the dedicated sender configured in Loop)
      - One of: `recipient: string (E164 phone or email)` OR `group: { group_id: string }`
    - Optional:
      - `reply_to_id: string` — reply in an existing thread
      - `passthrough: string` — user-defined correlation payload echoed back in webhooks
      - `service: "imessage" | "sms"` — delivery type hint
      - `timeout: number (>=5)` — sending timeout seconds
      - `status_callback: string (URL)` — per-message webhook URL override
      - `status_callback_header: string` — additional authorization header value for callback
      - `sandbox: boolean` — mark message for sandbox participants
    - Example:
```json
{
  "text": "Hello from Chip!",
  "sender_name": "sender@example.com",
  "recipient": "+13231112233",
  "reply_to_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "passthrough": "order=123",
  "service": "imessage",
  "timeout": 15
}
```
  - Request JSON (group text):
```json
{
  "text": "Welcome everyone",
  "sender_name": "sender@example.com",
  "group": { "group_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b" }
}
```
  - Request JSON (audio message):
```json
{
  "audio": { "url": "https://example.com/file.m4a" },
  "text": "(voice note)",
  "sender_name": "sender@example.com",
  "recipient": "+13231112233"
}
```
  - Request JSON (reaction):
```json
{
  "reaction": "like",
  "sender_name": "sender@example.com",
  "reply_to_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "recipient": "+13231112233"
}
```
  - Response JSON: returns JSON including a `message_id` and request metadata (exact fields may vary). Handle 4xx/5xx with error details.

Notes:
- The concrete path is configured in this repo as `https://server.loopmessage.com/api/v1/message/send/`.
- Payload variations above are consolidated for mocking; consult official docs for limits and full constraints.

---

## Webhooks (Inbound ← Loop)
Loop will `POST` JSON to our webhook URL. We must return `200 OK` fast; any other status triggers retries up to 30 times with increasing delays.

- Headers (incoming to us):
  - `Content-Type: application/json`
  - `User-Agent: LoopServer`
  - `Connection: close`
  - `Authorization: <optional token>` — if configured; verify on our side

- Response (from us back to Loop):
  - Status: `200 OK` ASAP (within 15 seconds)
  - Optional JSON body to control UX:
```json
{ "typing": 5, "read": true }
```
  - `typing: number (1..60)` — show typing indicator for N seconds
  - `read: boolean` — mark chat as read

### Webhook Event Types and Example Payloads
- Inbound text
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
- Message scheduled
```json
{
  "alert_type": "message_scheduled",
  "recipient": "+13231112233",
  "text": "text",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```
- Message failed
```json
{
  "alert_type": "message_failed",
  "recipient": "+13231112233",
  "text": "text",
  "error_code": 100,
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```
- Message sent
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
- Message reaction
```json
{
  "alert_type": "message_reaction",
  "recipient": "+13231112233",
  "text": "text",
  "reaction": "like",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```
- Message timeout
```json
{
  "alert_type": "message_timeout",
  "recipient": "+13231112233",
  "text": "text",
  "error_code": 130,
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b",
  "api_version": "1.0"
}
```
- Group created
```json
{
  "alert_type": "group_created",
  "group": {
    "group_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
    "name": "Group name",
    "participants": ["+13231112233", "+13233332211", "user@example.com"]
  },
  "recipient": "+13231112233",
  "sender_name": "sender@example.com",
  "text": "text",
  "message_id": "59c55Ce8-41d6-43Cc-9116-8cfb2e696D7b",
  "webhook_id": "ab5Ae733-cCFc-4025-9987-7279b26bE71b"
}
```
- Conversation initiated (legacy accounts)
```json
{ "alert_type": "conversation_inited", "recipient": "+13231112233", "sender_name": "sender@example.com" }
```
- Unknown
```json
{ "alert_type": "unknown", "recipient": "+13231112233" }
```

### Possible JSON fields in webhooks (selected)
- `message_id: string` — unique id of request/message
- `webhook_id: string` — unique id of the event
- `alert_type: string` — see event types
- `success: boolean | null` — only for `message_sent`
- `recipient: string` — E164 phone or lowercase email
- `text: string` — message text
- `subject: string` — optional
- `attachments: string[]` — only for `message_inbound`
- `message_type: "text" | "reaction" | "audio" | "attachments" | "sticker" | "location"`
- `delivery_type: "imessage" | "sms"`
- `reaction: "love" | "like" | "dislike" | "laugh" | "exclaim" | "question" | "unknown"`
- `thread_id: string` — optional iMessage thread identifier
- `sandbox: boolean` — optional (sandbox-only contacts)
- `sender_name: string` — dedicated sender name
- `error_code: number` — for `message_failed` and `message_timeout`
- `passthrough: string` — echoes back what was sent in request
- `language: { code: string, name: string, script?: "Hans" | "Hant" }`
- `group: { group_id: string, name?: string, participants: string[] }`
- `speech: { text: string, language: object, metadata?: { speaking_rate: number, average_pause_duration: number, speech_start_timestamp: number, speech_duration: number, jitter: number, shimmer: number, pitch: number, voicing: number } }`

### Error Codes (from webhooks)
- `100` — Internal error
- `110` — Unable delivery message
- `120` — Message sent unsuccessfully
- `130` — Message timeout
- `140` — Integration timeout/overloaded
- `150` — Failed to pass request to integration or integration error

---

## Information Flows (for mocking)

### A) Inbound message → Our reply
1. Loop → POST webhook (`message_inbound`)
2. Our server → respond 200 quickly; optionally `{ "typing": N, "read": true }`
3. Our server → POST send text to Loop
4. Loop → POST webhooks: `message_scheduled` → `message_sent { success: true|false }` or `message_failed`

### B) Outbound send (individual)
1. Our server → POST send text with `recipient`
2. Loop → `message_scheduled` → `message_sent` or `message_failed`/`message_timeout`

### C) Outbound send (group)
1. Our server → POST send text with `group.group_id`
2. Loop → `message_scheduled` → `message_sent` or `message_failed`

### D) Reaction to a message
1. Our server → POST send reaction with `reaction` and `reply_to_id`
2. Loop → `message_reaction`

### E) Audio inbound + speech transcript
1. Loop → `message_inbound` with `message_type: "audio"` and `speech` on success
2. Our server handles transcript; may reply as in A)

### F) Group created
1. Loop → `group_created` webhook with `group` object
2. Our server may store `group_id` and seed group context

### Retry/Timing
- Return `200` in ≤ 15 seconds (prefer < 1s). Loop retries up to 30 times on non-200.
- First 10 retries every 30s, next 10 every 3m, last 10 every 15m.

References: [Webhooks/Callbacks](https://docs.loopmessage.com/imessage-conversation-api/webhooks)

---

## Mock Server Contract (proposed)
- Outbound endpoint: `POST /api/v1/message/send/`
  - Validate headers and payload combinations above
  - Generate `message_id` and echo `passthrough`
  - Schedule webhook emissions to our app according to a scenario script
- Webhook dispatcher: `POST /webhooks/loop`
  - Accept inbound emissions from the mock engine to simulate Loop behavior
  - Support `typing` and `read` fields in our app’s response, but the mock needn’t enforce timing
- Scenario engine:
  - State machine per `message_id`/`recipient`/`group_id`
  - Deterministic seeds to produce sequences (scheduled → sent(success) vs failed, timeouts, reactions)
  - Clock control to advance time and trigger retries/backoff

---

## JSON Schemas (for validation — simplified)

### Send Text (request)
```json
{
  "type": "object",
  "required": ["sender_name"],
  "oneOf": [
    { "required": ["text", "recipient"] },
    { "required": ["text", "group"] },
    { "required": ["reaction", "reply_to_id", "recipient"] },
    { "required": ["audio", "recipient"] }
  ],
  "properties": {
    "text": { "type": "string" },
    "audio": { "type": "object", "properties": { "url": { "type": "string", "format": "uri" } }, "required": ["url"] },
    "reaction": { "type": "string", "enum": ["love","like","dislike","laugh","exclaim","question","unknown"] },
    "reply_to_id": { "type": "string" },
    "recipient": { "type": "string" },
    "group": { "type": "object", "properties": { "group_id": { "type": "string" } }, "required": ["group_id"] },
    "sender_name": { "type": "string" },
    "passthrough": { "type": "string" },
    "service": { "type": "string", "enum": ["imessage","sms"] },
    "timeout": { "type": "integer", "minimum": 5 },
    "status_callback": { "type": "string", "format": "uri" },
    "status_callback_header": { "type": "string" },
    "sandbox": { "type": "boolean" }
  }
}
```

### Webhook Event (base + examples)
- Base envelope has at minimum `alert_type`, and often includes `message_id`, `webhook_id`, `recipient`, and fields listed above. Use the event examples verbatim for scenario fixtures.

---

## Test Scenarios (examples)
- **Happy path (individual)**: inbound text → typing(5) → outbound send → scheduled → sent(success=true)
- **Delivery failure**: outbound send → scheduled → failed(error_code=110)
- **Timeout**: outbound send(timeout=5) → timeout(error_code=130)
- **Reaction**: user reacts to our message → `message_reaction` inbound
- **Group onboarding**: `group_created` → outbound welcome → scheduled → sent
- **Sandbox flow**: send with `sandbox=true` and verify webhook flags
- **Audio inbound**: inbound with `message_type="audio"` + `speech` object
- **Retry semantics**: simulate our app returning non-200 once; verify mock retries with same `webhook_id`

---

## Implementation Notes
- Prefer fixture libraries that can emit the exact JSONs above, with jittered timestamps and stable IDs per scenario.
- Keep recipient identifiers masked in logs. Avoid logging full E164 values.
- Make the mock deterministic by default; add chaos flags to randomize failures/timeouts.

## Test Coverage Implemented in Repo

- Normalization of native Loop webhook shape and internal testing shape
- Verification via `Authorization` header for inbound webhooks
- Outbound send payload combinations validated against examples using `respx` to assert HTTP
- Scenario stubs for message inbound → immediate reply/send

References:
- [Webhooks/Callbacks](https://docs.loopmessage.com/imessage-conversation-api/webhooks)
- [Sending Messages](https://docs.loopmessage.com/imessage-conversation-api/send-message)
- [Statuses](https://docs.loopmessage.com/imessage-conversation-api/statuses)
