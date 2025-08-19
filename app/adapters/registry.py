from __future__ import annotations

from typing import Dict

from app.adapters.base import MessagingAdapter
from app.adapters.loop import LoopClient


class AdapterRegistry:
    """Registry for messaging adapters by name.

    Enables plugging in alternative providers like Twilio or WhatsApp later
    without changing router logic.
    """

    _registry: Dict[str, type[MessagingAdapter]] = {
        "loop": LoopClient,
    }

    @classmethod
    def get(cls, name: str) -> MessagingAdapter:
        provider_cls = cls._registry.get(name)
        if provider_cls is None:
            raise KeyError(f"Unknown messaging adapter: {name}")
        return provider_cls()

    @classmethod
    def register(cls, name: str, adapter_cls: type[MessagingAdapter]) -> None:
        cls._registry[name] = adapter_cls

