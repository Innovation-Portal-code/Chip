from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import httpx

from app.adapters.base import MessagingAdapter
from app.config import get_settings
from app.models.messages import IncomingMessage, OutgoingMessage


class LoopClient:
    """Client for LoopMessage iMessage Conversation API (send only).

    Outbound endpoint (consolidated): POST /api/v1/message/send/
    Ref: LoopMessage-iMessage-API-Mock-Spec.md
    """

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.LOOP_API_BASE_URL
        self.api_key = api_key or settings.LOOP_API_KEY

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key
        return headers

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        settings = get_settings()
        if not self.base_url or not self.api_key or settings.ENV != "prod":
            # Dev/test fallback: log-only to avoid network in local & tests
            print({"loop_dev_send": True, "env": settings.ENV, "payload": payload})
            return {"status": "logged", "message_id": payload.get("message_id")}
        url = f"{self.base_url.rstrip('/')}/message/send/"
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            return resp.json()


class LoopAdapter(MessagingAdapter):
    provider_name = "loop"

    def __init__(self, client: Optional[LoopClient] = None) -> None:
        self.client = client or LoopClient()

    def normalize_inbound(self, payload: Dict[str, Any]) -> IncomingMessage:
        alert_type = payload.get("alert_type")
        message_type = payload.get("message_type")
        incoming = IncomingMessage(
            provider=self.provider_name,
            message_id=payload.get("message_id"),
            thread_id=payload.get("thread_id"),
            sender_address=payload.get("sender_name"),
            recipient_address=payload.get("recipient"),
            text=payload.get("text"),
            message_type=message_type,
            delivery_type=payload.get("delivery_type"),
            reaction=payload.get("reaction"),
            sandbox=payload.get("sandbox"),
            group_id=(payload.get("group") or {}).get("group_id")
            if payload.get("group")
            else None,
            group_name=(payload.get("group") or {}).get("name")
            if payload.get("group")
            else None,
            attachments=payload.get("attachments"),
            raw=payload,
        )
        return incoming

    def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "sender_name": os.environ.get("LOOP_SENDER_NAME", "sender@example.com"),
        }
        if message.group_id:
            payload.update(
                {
                    "text": message.text or "",
                    "group": {"group_id": message.group_id},
                }
            )
        elif message.reaction:
            payload.update(
                {
                    "reaction": message.reaction,
                    "reply_to_id": message.reply_to_id,
                    "recipient": message.to,
                }
            )
        elif message.audio_url:
            payload.update(
                {
                    "audio": {"url": message.audio_url},
                    "text": message.text or "",
                    "recipient": message.to,
                }
            )
        else:
            payload.update(
                {
                    "text": message.text or "",
                    "recipient": message.to,
                }
            )

        if message.passthrough:
            payload["passthrough"] = message.passthrough
        if message.service:
            payload["service"] = message.service

        return self.client.send(payload)

    def verify_signature(self, headers: Dict[str, str], body_bytes: bytes) -> bool:
        # Use environment directly to allow runtime/test overrides without cached settings
        secret = os.environ.get("LOOP_WEBHOOK_SECRET")
        if not secret:
            return True
        # Accept common casings
        auth = headers.get("Authorization") or headers.get("authorization")
        return auth == secret
