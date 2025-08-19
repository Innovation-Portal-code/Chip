import os
from typing import Optional


class Settings:
    """Simple environment-backed settings.

    Avoids external deps to keep tests lightweight. If a value is missing,
    callers should handle sensible defaults.
    """

    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        groq_model: str = "llama-3.1-70b-versatile",
        openai_api_base: str = "https://api.groq.com/openai/v1",
        loop_api_base_url: str = "https://server.loopmessage.com/api/v1",
        loop_api_key: Optional[str] = None,
        loop_webhook_secret: Optional[str] = None,
        use_dspy: bool = False,
        environment: str = os.environ.get("ENV", "dev"),
    ) -> None:
        self.GROQ_API_KEY = groq_api_key
        self.GROQ_MODEL = groq_model
        self.OPENAI_API_BASE = openai_api_base
        self.LOOP_API_BASE_URL = loop_api_base_url
        self.LOOP_API_KEY = loop_api_key
        self.LOOP_WEBHOOK_SECRET = loop_webhook_secret
        self.USE_DSPY = use_dspy
        self.ENV = environment


_cached_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _cached_settings
    if _cached_settings is None:
        _cached_settings = Settings(
            groq_api_key=os.environ.get("GROQ_API_KEY"),
            groq_model=os.environ.get("GROQ_MODEL", "llama-3.1-70b-versatile"),
            openai_api_base=os.environ.get("OPENAI_API_BASE", "https://api.groq.com/openai/v1"),
            loop_api_base_url=os.environ.get("LOOP_API_BASE_URL", "https://server.loopmessage.com/api/v1"),
            loop_api_key=os.environ.get("LOOP_API_KEY"),
            loop_webhook_secret=os.environ.get("LOOP_WEBHOOK_SECRET"),
            use_dspy=os.environ.get("USE_DSPY", "false").lower() in {"1", "true", "yes"},
            environment=os.environ.get("ENV", "dev"),
        )
    return _cached_settings

