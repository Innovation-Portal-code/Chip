from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient


def test_webhook_inbound_echo_reply(monkeypatch, client: TestClient) -> None:
    # Stub adapter client send to avoid network
    from app.adapters import loop as loop_mod

    class CapturingClient(loop_mod.LoopClient):
        def __init__(self):
            self.sent_payloads = []

        def send(self, payload):  # type: ignore[override]
            self.sent_payloads.append(payload)
            return {"ok": True}

    captured = CapturingClient()

    class PatchedLoopAdapter(loop_mod.LoopAdapter):
        def __init__(self, *a, **k):
            super().__init__(client=captured)

    monkeypatch.setattr(loop_mod, "LoopAdapter", PatchedLoopAdapter)

    payload: Dict[str, Any] = {
        "alert_type": "message_inbound",
        "recipient": "+13231112233",
        "text": "Hello from user",
        "message_type": "text",
        "message_id": "msg-1",
        "webhook_id": "wh-1",
        "api_version": "1.0",
    }

    r = client.post("/webhooks/loop", json=payload)
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert len(captured.sent_payloads) == 1
    out = captured.sent_payloads[0]
    assert out["recipient"] == "+13231112233"
    assert isinstance(out["text"], str) and len(out["text"]) > 0
