from __future__ import annotations

from typing import Any, Dict, Optional, Protocol


class MessagingAdapter(Protocol):
    """Protocol for messaging providers.

    Concrete implementations should encapsulate provider-specific HTTP and
    webhook normalization so routers can remain provider-agnostic.
    """

    def send_text(
        self,
        *,
        recipient: Optional[str] = None,
        text: str,
        group_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        passthrough: Optional[str] = None,
        service: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        ...

    def verify_request(self, authorization_header: Optional[str]) -> None:
        """Raise if the incoming webhook request is not authorized."""
        ...

    def normalize_event(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an inbound webhook payload to a common shape.

        Returns a dictionary with at least keys: text, recipient (optional),
        message_id (optional), group_id (optional).
        """
        ...

