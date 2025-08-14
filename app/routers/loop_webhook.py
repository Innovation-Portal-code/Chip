import os
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel


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
    expected = os.getenv("LOOP_WEBHOOK_AUTH")
    if expected:
        if not authorization or authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized webhook")

    body = await request.json()

    # Best-effort normalization for logging and M1 echo behavior
    # Handle Loop's documented schema first (alert_type, text, recipient, ...)
    if isinstance(body, dict) and body.get("alert_type"):
        alert_type = body.get("alert_type")
        text = body.get("text", "")
        recipient = body.get("recipient")
        message_id = body.get("message_id")
        group = body.get("group") if isinstance(body.get("group"), dict) else None
        conversation_id = (
            group.get("group_id") if isinstance(group, dict) else message_id
        )
        return {
            "ok": True,
            "alert_type": alert_type,
            "recipient": recipient,
            "message_id": message_id,
            "received_text": text,
            "conversation_id": conversation_id,
        }

    # Otherwise, support the internal event/data/message shape used for local testing
    try:
        event = LoopEvent.model_validate(body)
    except Exception:
        event = LoopEvent(event=str(body.get("event", "")), data=body.get("data", {}))

    message: dict[str, Any] = (
        event.data.get("message", {}) if isinstance(event.data, dict) else {}
    )
    text: str = message.get("text", "")
    conversation_id: str | None = (
        event.data.get("conversationId") if isinstance(event.data, dict) else None
    )

    # M1 behavior: acknowledge and echo basic info
    return {
        "ok": True,
        "received_text": text,
        "conversation_id": conversation_id,
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
