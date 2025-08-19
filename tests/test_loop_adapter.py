from __future__ import annotations

import json
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.adapters.loop import LoopAdapter, LoopClient
from app.models.messages import OutgoingMessage


def test_loop_adapter_normalize_inbound_text() -> None:
    payload: Dict[str, Any] = {
        "alert_type": "message_inbound",
        "recipient": "+13231112233",
        "text": "hello",
        "message_type": "text",
        "message_id": "m1",
        "webhook_id": "w1",
        "api_version": "1.0",
    }
    adapter = LoopAdapter()
    msg = adapter.normalize_inbound(payload)
    assert msg.provider == "loop"
    assert msg.recipient_address == "+13231112233"
    assert msg.text == "hello"
    assert msg.message_type == "text"


class DummyClient(LoopClient):
    def __init__(self) -> None:
        pass

    def send(self, payload):  # type: ignore[override]
        # just echo for tests
        return {"ok": True, "echo": payload}


def test_loop_adapter_send_text(monkeypatch) -> None:
    adapter = LoopAdapter(client=DummyClient())
    out = OutgoingMessage(to="+15551230000", text="Hi")
    resp = adapter.send_message(out)
    assert resp["ok"] is True
    assert resp["echo"]["text"] == "Hi"
    assert resp["echo"]["recipient"] == "+15551230000"


def test_loop_adapter_send_reaction() -> None:
    adapter = LoopAdapter(client=DummyClient())
    out = OutgoingMessage(to="+1555", reaction="like", reply_to_id="abc")
    resp = adapter.send_message(out)
    echo = resp["echo"]
    assert echo["reaction"] == "like"
    assert echo["reply_to_id"] == "abc"
    assert echo["recipient"] == "+1555"


def test_loop_adapter_send_audio() -> None:
    adapter = LoopAdapter(client=DummyClient())
    out = OutgoingMessage(to="+1555", audio_url="https://example.com/a.m4a", text="(voice note)")
    resp = adapter.send_message(out)
    echo = resp["echo"]
    assert echo["audio"]["url"].endswith("a.m4a")
    assert echo["text"] == "(voice note)"
    assert echo["recipient"] == "+1555"


def test_loop_adapter_send_group() -> None:
    adapter = LoopAdapter(client=DummyClient())
    out = OutgoingMessage(to="ignored", text="Welcome", group_id="g-1")
    resp = adapter.send_message(out)
    echo = resp["echo"]
    assert echo["group"]["group_id"] == "g-1"
    assert echo["text"] == "Welcome"


