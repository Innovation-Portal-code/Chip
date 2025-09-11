import pytest
from fastapi.testclient import TestClient

from app.server import create_app


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "test")
    # Safe defaults for Loop adapter
    monkeypatch.setenv(
        "LOOP_SEND_URL", "https://server.loopmessage.com/api/v1/message/send/"
    )
    monkeypatch.setenv("LOOP_AUTHORIZATION", "test-auth")
    monkeypatch.setenv("LOOP_SECRET_KEY", "test-secret")
    monkeypatch.setenv("LOOP_SENDER_NAME", "sender@example.com")
    monkeypatch.setenv("LOOP_WEBHOOK_AUTH", "inbound-secret")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())
