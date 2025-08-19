from __future__ import annotations

from typing import Any, Dict

import pytest

from app.adapters.loop import LoopAdapter


@pytest.mark.parametrize(
    "payload",
    [
        {
            "alert_type": "message_scheduled",
            "recipient": "+13231112233",
            "text": "text",
            "message_id": "m1",
            "webhook_id": "w1",
            "api_version": "1.0",
        },
        {
            "alert_type": "message_sent",
            "success": True,
            "recipient": "+13231112233",
            "text": "text",
            "message_id": "m1",
            "webhook_id": "w1",
            "api_version": "1.0",
        },
        {
            "alert_type": "message_failed",
            "recipient": "+13231112233",
            "text": "text",
            "error_code": 110,
            "message_id": "m1",
            "webhook_id": "w1",
            "api_version": "1.0",
        },
        {
            "alert_type": "message_timeout",
            "recipient": "+13231112233",
            "text": "text",
            "error_code": 130,
            "message_id": "m1",
            "webhook_id": "w1",
            "api_version": "1.0",
        },
        {
            "alert_type": "message_reaction",
            "recipient": "+13231112233",
            "text": "text",
            "reaction": "like",
            "message_id": "m1",
            "webhook_id": "w1",
            "api_version": "1.0",
        },
        {
            "alert_type": "group_created",
            "group": {
                "group_id": "g1",
                "name": "Group name",
                "participants": ["+13231112233", "+13233332211", "user@example.com"],
            },
            "recipient": "+13231112233",
            "sender_name": "sender@example.com",
            "text": "text",
            "message_id": "m1",
            "webhook_id": "w1",
        },
    ],
)
def test_loop_normalize_various(payload: Dict[str, Any]) -> None:
    adapter = LoopAdapter()
    msg = adapter.normalize_inbound(payload)
    assert msg.provider == "loop"
    # Ensure doesn't crash and captures base fields when present
    if "recipient" in payload:
        assert msg.recipient_address == payload["recipient"]

