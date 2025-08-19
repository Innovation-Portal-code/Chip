from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class IncomingMessage(BaseModel):
    """Normalized inbound message across providers."""

    provider: str
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    sender_address: Optional[str] = None
    recipient_address: Optional[str] = None
    text: Optional[str] = None
    message_type: Optional[str] = None
    delivery_type: Optional[str] = None
    reaction: Optional[str] = None
    sandbox: Optional[bool] = None
    group_id: Optional[str] = None
    group_name: Optional[str] = None
    attachments: Optional[List[str]] = None
    raw: Dict[str, Any] = {}


class OutgoingMessage(BaseModel):
    """Normalized outbound message."""

    to: str
    text: Optional[str] = None
    reply_to_id: Optional[str] = None
    passthrough: Optional[str] = None
    service: Optional[str] = None  # "imessage" | "sms"
    group_id: Optional[str] = None
    audio_url: Optional[str] = None
    reaction: Optional[str] = None


