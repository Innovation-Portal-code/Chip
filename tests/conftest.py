import os
import types
from contextlib import contextmanager
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "test")
    # Safe defaults for Loop adapter
    monkeypatch.setenv("LOOP_SEND_URL", "https://server.loopmessage.com/api/v1/message/send/")
    monkeypatch.setenv("LOOP_AUTHORIZATION", "test-auth")
    monkeypatch.setenv("LOOP_SECRET_KEY", "test-secret")
    monkeypatch.setenv("LOOP_SENDER_NAME", "sender@example.com")
    monkeypatch.setenv("LOOP_WEBHOOK_AUTH", "inbound-secret")


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@contextmanager
def override_generate_reply(fake_text: str) -> Generator[None, None, None]:
    from app.agents import dspy_agent as agent_module

    original = agent_module.generate_reply

    def _fake(user_message: str) -> str:  # type: ignore[override]
        return fake_text

    agent_module.generate_reply = _fake  # type: ignore[assignment]
    try:
        yield
    finally:
        agent_module.generate_reply = original  # type: ignore[assignment]

