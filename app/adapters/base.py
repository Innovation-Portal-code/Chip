from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.models.messages import IncomingMessage, OutgoingMessage


class MessagingAdapter(ABC):
    """Abstract base for messaging providers.

    Implementations must:
    - Normalize inbound webhook payloads
    - Send outbound messages
    - Optionally verify webhook signatures/headers
    """

    provider_name: str

    @abstractmethod
    def normalize_inbound(self, payload: Dict[str, Any]) -> IncomingMessage:
        raise NotImplementedError

    @abstractmethod
    def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        raise NotImplementedError

    def verify_signature(self, headers: Dict[str, str], body_bytes: bytes) -> bool:
        return True

