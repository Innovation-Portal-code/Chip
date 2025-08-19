import os
from typing import Any, Dict, Optional

import httpx

from app.adapters.base import MessagingAdapter


class LoopClient(MessagingAdapter):
    """LoopMessage adapter implementing the MessagingAdapter protocol.

    Sends text messages to an individual recipient (phone/email) or a group.
    Also provides webhook verification and normalization helpers.
    """

    def __init__(self) -> None:
        self.send_url = os.getenv(
            "LOOP_SEND_URL", "https://server.loopmessage.com/api/v1/message/send/"
        )
        self.authorization = os.environ.get("LOOP_AUTHORIZATION", "")
        self.secret_key = os.environ.get("LOOP_SECRET_KEY", "")
        self.sender_name = os.environ.get("LOOP_SENDER_NAME", "")
        self.status_callback = os.environ.get("STATUS_CALLBACK_URL")
        self.status_callback_auth = os.environ.get("STATUS_CALLBACK_AUTH")
        self.webhook_auth = os.environ.get("LOOP_WEBHOOK_AUTH")

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Authorization": self.authorization,
            "Loop-Secret-Key": self.secret_key,
            "Content-Type": "application/json",
        }
        return headers

    def send_text(
        self,
        *,
        recipient: Optional[str] = None,
        text: str,
        group_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        passthrough: Optional[str] = None,
        service: Optional[str] = None,  # "imessage" or "sms"
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a text message via Loop.

        Either `recipient` or `group_id` must be provided.
        """
        if not self.authorization or not self.secret_key:
            raise RuntimeError(
                "Missing LOOP_AUTHORIZATION or LOOP_SECRET_KEY environment variables"
            )
        if not self.sender_name:
            raise RuntimeError("Missing LOOP_SENDER_NAME environment variable")
        if not recipient and not group_id:
            raise ValueError("Either recipient or group_id must be provided")

        payload: Dict[str, Any] = {
            "text": text,
            "sender_name": self.sender_name,
        }
        if recipient:
            payload["recipient"] = recipient
        if group_id:
            payload["group"] = {"group_id": group_id}
        if self.status_callback:
            payload["status_callback"] = self.status_callback
        if self.status_callback_auth:
            payload["status_callback_header"] = self.status_callback_auth
        if reply_to_id:
            payload["reply_to_id"] = reply_to_id
        if passthrough:
            payload["passthrough"] = passthrough
        if service:
            payload["service"] = service
        if timeout_seconds and timeout_seconds >= 5:
            payload["timeout"] = timeout_seconds

        with httpx.Client(timeout=15) as client:
            response = client.post(self.send_url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    # Webhook helpers
    def verify_request(self, authorization_header: Optional[str]) -> None:
        if not self.webhook_auth:
            return
        if not authorization_header or authorization_header != self.webhook_auth:
            raise PermissionError("Unauthorized webhook")

    def normalize_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        # Native Loop webhook shape
        if isinstance(body, dict) and body.get("alert_type"):
            group = body.get("group") if isinstance(body.get("group"), dict) else None
            return {
                "alert_type": body.get("alert_type"),
                "text": body.get("text", ""),
                "recipient": body.get("recipient"),
                "message_id": body.get("message_id"),
                "group_id": group.get("group_id") if isinstance(group, dict) else None,
            }

        # Internal testing shape from plan
        data = body.get("data", {}) if isinstance(body, dict) else {}
        message = data.get("message", {}) if isinstance(data, dict) else {}
        return {
            "alert_type": body.get("event"),
            "text": message.get("text", ""),
            "recipient": message.get("from", {}).get("address")
            if isinstance(message.get("from"), dict)
            else None,
            "message_id": message.get("id"),
            "group_id": data.get("conversationId") if isinstance(data, dict) else None,
        }
