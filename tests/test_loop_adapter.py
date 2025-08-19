from __future__ import annotations

import json

import httpx
import pytest
import respx

from app.adapters.loop import LoopClient


@respx.mock
def test_send_text_individual_success() -> None:
    client = LoopClient()

    route = respx.post(client.send_url).mock(
        return_value=httpx.Response(200, json={"message_id": "m1", "ok": True})
    )

    resp = client.send_text(recipient="+15551234567", text="Hello!")

    assert route.called
    sent = json.loads(route.calls.last.request.content.decode())
    assert sent["text"] == "Hello!"
    assert sent["recipient"] == "+15551234567"
    assert sent["sender_name"]
    assert resp["message_id"] == "m1"


@respx.mock
def test_send_text_group_with_reply_and_timeout() -> None:
    client = LoopClient()

    route = respx.post(client.send_url).mock(
        return_value=httpx.Response(200, json={"message_id": "g1"})
    )

    resp = client.send_text(
        group_id="group-123",
        text="Welcome",
        reply_to_id="prior-1",
        passthrough="trace=abc",
        service="imessage",
        timeout_seconds=10,
    )

    assert route.called
    payload = json.loads(route.calls.last.request.content.decode())
    assert payload["group"]["group_id"] == "group-123"
    assert payload["reply_to_id"] == "prior-1"
    assert payload["passthrough"] == "trace=abc"
    assert payload["service"] == "imessage"
    assert payload["timeout"] == 10
    assert resp["message_id"] == "g1"


def test_send_text_requires_sender_and_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOOP_AUTHORIZATION", raising=False)
    client = LoopClient()
    with pytest.raises(RuntimeError):
        client.send_text(recipient="x", text="y")

