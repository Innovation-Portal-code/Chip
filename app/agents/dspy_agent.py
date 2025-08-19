from __future__ import annotations

import os
from typing import Optional


class MockAgent:
    """Lightweight stand-in for DSPy+Groq.

    In tests and local dev without Groq, returns a templated reply.
    """

    def respond(self, user_message: str) -> str:
        user_message = (user_message or "").strip()
        if not user_message:
            return "Hi! How can I help today?"
        return f"You said: {user_message}. Here's a helpful reply from Chip."


_agent: Optional[MockAgent] = None


def generate_reply(user_message: str) -> str:
    global _agent
    if _agent is None:
        _agent = MockAgent()
    return _agent.respond(user_message)

