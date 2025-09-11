### Next steps to begin executing Plan.md (short, actionable)

- [ ] Foundation: add missing deps in pyproject
  - pydantic-ai-slim[mcp], logfire, temporalio, twilio (for SMS later), uvicorn (optional)
  - update project and readme to use uvicorn for dev server
  - remove dspy-ai dependency
- [ ] Observability: wire Logfire
  - Initialize at startup, instrument FastAPI, add redaction defaults and correlation ids
- [ ] Env & DX: create .env.example and quickstart
  - LOOP_AUTHORIZATION, LOOP_SECRET_KEY, LOOP_SENDER_NAME, LOOP_WEBHOOK_AUTH, STATUS_CALLBACK_URL/STATUS_CALLBACK_AUTH, GROQ_API_KEY or OPENAI_API_KEY, SUPABASE_URL/SUPABASE_KEY
- [ ] Webhook: align handler with tests and Plan
  - Call agent for reply; return {ok, received_text, reply, sent}; keep closed-failure auth
- [ ] Agent: migrate to Pydantic AI (remove DSPy)
  - Remove `app/agents/dspy_agent.py` and deprecate `/test/agent` route (replace with simple Pydantic AI ping route if needed)
  - Add minimal Pydantic AI agent module with typed tool (welcome/echo) and system prompt per Plan/Research; swap webhook to call it
  - Expose agent via injectable interface for tests (dependency override)
- [ ] Loop adapter: idempotency and headers
  - Generate and send Idempotency-Key; surface in SendResult for audit
- [ ] Storage: stub durable writes for inbound/outbound events
  - Define interface + minimal Supabase schema; store raw + normalized payloads
- [ ] Tests: refactor to new agent and behaviors
  - Replace `override_generate_reply` with DI override for agent; assert response contract; remove DSPy-specific imports
- [ ] Scripts: local run commands
  - uv run uvicorn main:app --host 0.0.0.0 --port 8000; tests (pytest); lint (ruff)
- [ ] CI: basic workflow
  - Run ruff + pytest on PR; cache uv
- [ ] Cleanup: remove dead code/docs tied to DSPy and update README

Notes
- Removals/refactors are expected: prefer typed interfaces and Pydantic AI per Plan/Research.
- Prioritize: Logfire + webhook agent call + idempotency; storage can be a thin stub first.
- Twilio adapter skeleton can follow to set up SMS fallback in the next phase.
