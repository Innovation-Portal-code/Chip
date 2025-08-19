import pytest

from app.adapters.registry import AdapterRegistry
from app.adapters.base import MessagingAdapter


class DummyAdapter:
    def __init__(self) -> None:
        self.sent = []

    def send_text(self, **kwargs):  # type: ignore[no-untyped-def]
        self.sent.append(kwargs)
        return {"ok": True}

    def verify_request(self, authorization_header):  # type: ignore[no-untyped-def]
        return None

    def normalize_event(self, body):  # type: ignore[no-untyped-def]
        return body


def test_registry_get_and_register() -> None:
    # loop is pre-registered
    adapter = AdapterRegistry.get("loop")
    assert hasattr(adapter, "send_text")

    # register custom
    AdapterRegistry.register("dummy", DummyAdapter)  # type: ignore[arg-type]
    d = AdapterRegistry.get("dummy")
    assert isinstance(d, DummyAdapter)


def test_registry_unknown() -> None:
    with pytest.raises(KeyError):
        AdapterRegistry.get("missing")

