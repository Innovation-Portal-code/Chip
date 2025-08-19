import os
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from app.adapters.registry import AdapterRegistry
from app.agents import dspy_agent as agent_module


router = APIRouter(prefix="", tags=["loop"])


class LoopMessage(BaseModel):
    id: Optional[str] = None
    text: str
    from_: Optional[dict[str, Any]] = None  # using from_ to avoid keyword clash
    to: Optional[dict[str, Any]] = None

    class Config:
        fields = {"from_": "from"}


class LoopEvent(BaseModel):
    event: str
    data: dict[str, Any]


@router.post("/webhooks/loop")
async def loop_webhook(
    request: Request,
    authorization: str | None = Header(default=None, convert_underscores=False),
):
    adapter = AdapterRegistry.get("loop")

    # Verify webhook
    try:
        adapter.verify_request(authorization)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Unauthorized webhook")

    body = await request.json()
    normalized = adapter.normalize_event(body if isinstance(body, dict) else {})

    text = normalized.get("text", "")
    recipient = normalized.get("recipient")
    message_id = normalized.get("message_id")
    conversation_id = normalized.get("group_id") or message_id

    # Generate reply
    try:
        reply_text = agent_module.generate_reply(user_message=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    # If we have a recipient, attempt to send via adapter
    sent = None
    if recipient:
        try:
            sent = adapter.send_text(
                recipient=recipient,
                text=reply_text,
                group_id=conversation_id,
                reply_to_id=message_id,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Send error: {e}")

    return {
        "ok": True,
        "received_text": text,
        "conversation_id": conversation_id,
        "reply": reply_text,
        "sent": sent,
    }


class TestSendRequest(BaseModel):
    to: str
    text: str
    conversation_id: Optional[str] = None


@router.post("/test/send")
async def test_send(payload: TestSendRequest):
    # For M1, we don't send to Loop yet; just return normalized payload
    return {
        "ok": True,
        "to": payload.to,
        "text": payload.text,
        "conversation_id": payload.conversation_id,
    }
