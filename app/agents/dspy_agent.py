import os

import dspy


def _create_lm() -> dspy.LM:
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY or OPENAI_API_KEY for DSPy")

    model = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

    # DSPy wrapper for OpenAI-compatible endpoints
    lm = dspy.LM(model=model)
    return lm


_configured = False


def configure_dspy(
    input_token_limit: int = 8000, output_token_limit: int = 512
) -> None:
    global _configured
    if _configured:
        return
    lm = _create_lm()
    dspy.settings.configure(
        lm=lm,
        input_token_limit=input_token_limit,
        output_token_limit=output_token_limit,
    )
    _configured = True


class ChatSignature(dspy.Signature):
    """Respond as Chip, a helpful, friendly Alabama tech community agent.

    Chip is warm, concise, and practical. Prefer actionable next steps,
    short paragraphs, and a welcoming tone. If you don't know, say so and
    propose how to find out. Avoid over-promising.

    user_message: The latest user message from the user
    """

    user_message = dspy.InputField()
    reply = dspy.OutputField()


class ChipRespond(dspy.Module):
    def __init__(self) -> None:
        super().__init__()
        self.generate = dspy.Predict(ChatSignature)

    def forward(self, user_message: str) -> str:
        result = self.generate(user_message=user_message)
        return getattr(result, "reply", "")


def generate_reply(user_message: str) -> str:
    """Generate a reply from the Chip DSPy module.

    Persona is embedded in the module's signature; no external context needed.
    """
    configure_dspy()
    agent = ChipRespond()
    reply = agent(user_message=user_message)
    # `agent(...)` returns a string due to our `forward` implementation
    return reply or ""
