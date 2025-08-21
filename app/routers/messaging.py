from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Body, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


from app.adapters.registry import AdapterRegistry
from app.types import (
    NormalizedEvent,
    SendMessageRequest,
    SendMessageResponse,
    IMessageTextMessage,
)


router = APIRouter(prefix="", tags=["messaging"])
security = HTTPBearer(auto_error=False)


@router.post("/messages/send")
async def send_message(payload: SendMessageRequest) -> SendMessageResponse:
    adapter = AdapterRegistry.get(payload.provider)
    try:
        payload.message.ensure_valid_target()
        print(payload.message)
        result = adapter.send_message(payload.message)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Send error: {e}")
    return SendMessageResponse(ok=True, result=result)


@router.post("/webhooks/{provider}")
async def webhook_events(
    provider: str,
    payload: dict[str, Any] = Body(..., description="Raw webhook JSON payload"),
    credentials: HTTPAuthorizationCredentials | None = Security(security),
) -> dict[str, Any]:
    """Generic webhook handler for any provider.

    - Verifies the request using the adapter's `verify_request`
    - Normalizes inbound payload to `NormalizedEvent`
    - Calls the agent to generate replies
    - If a recipient is present, sends a text reply via the same adapter
    """
    adapter = AdapterRegistry.get(provider)

    try:
        token = credentials.credentials if credentials is not None else None
        adapter.verify_request(token)
    except PermissionError:
        raise HTTPException(status_code=401, detail="Unauthorized webhook")

    normalized: NormalizedEvent = adapter.normalize_event(
        payload if isinstance(payload, dict) else {}
    )

    recipient = normalized.recipient

    # Hard-coded welcome message for early users
    reply_text = (
        "Thanks for joining the network! You're one of the first to try this out. "
        "We're excited to have you onboard. More information and features will be shared soon—stay tuned!"
    )

    if recipient:
        try:
            adapter.send_message(
                IMessageTextMessage(
                    recipient=recipient,
                    text=reply_text,
                )
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Send error: {e}")

    return {
        "ok": True,
    }
