from __future__ import annotations

from fastapi import APIRouter, Request, Response

import app.adapters.loop as loop_mod
from app.agents.dspy_agent import generate_reply
from app.models.messages import OutgoingMessage


router = APIRouter()


@router.post("/webhooks/loop")
async def loop_webhook(request: Request) -> dict:
    body = await request.json()
    headers = {k: v for k, v in request.headers.items()}

    adapter = loop_mod.LoopAdapter()
    if not adapter.verify_signature(headers, (await request.body())):
        return {"ok": False, "error": "invalid signature"}

    incoming = adapter.normalize_inbound(body)

    # Immediate ack for Loop; optional typing/read could be returned here.
    # For v1, we generate a synchronous reply to keep flow simple.
    reply_text = generate_reply(incoming.text or "")
    if incoming.recipient_address:
        outgoing = OutgoingMessage(to=incoming.recipient_address, text=reply_text)
        adapter.send_message(outgoing)

    return {"ok": True}

