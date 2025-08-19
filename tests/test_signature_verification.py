from __future__ import annotations

from fastapi.testclient import TestClient


def test_signature_optional_allows_requests(monkeypatch, client: TestClient) -> None:
    # Default: no secret set, should accept
    payload = {
        "alert_type": "message_inbound",
        "recipient": "+1",
        "text": "hi",
        "message_type": "text",
    }
    r = client.post("/webhooks/loop", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_signature_enforced(monkeypatch, client: TestClient) -> None:
    monkeypatch.setenv("LOOP_WEBHOOK_SECRET", "s3cr3t")
    payload = {
        "alert_type": "message_inbound",
        "recipient": "+1",
        "text": "hi",
        "message_type": "text",
    }
    # Missing header -> should be rejected by our handler but we return 200 with ok False
    r = client.post("/webhooks/loop", json=payload)
    assert r.status_code == 200
    assert r.json()["ok"] is False

    # Now include correct header to pass verification
    r2 = client.post("/webhooks/loop", json=payload, headers={"Authorization": "s3cr3t"})
    assert r2.status_code == 200
    assert r2.json()["ok"] is True


