import os
import typing as t

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(autouse=True)
def _env_isolation(monkeypatch: pytest.MonkeyPatch) -> t.Iterator[None]:
    # Ensure deterministic tests and avoid real network calls by default
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("LOOP_API_BASE_URL", raising=False)
    monkeypatch.delenv("LOOP_API_KEY", raising=False)
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
