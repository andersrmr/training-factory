from langchain_openai import ChatOpenAI

from training_factory.settings import Settings, get_settings


def build_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create a ChatOpenAI client from settings."""

    cfg = settings or get_settings()
    if not cfg.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required to build ChatOpenAI")

    return ChatOpenAI(
        api_key=cfg.openai_api_key,
        model=cfg.openai_model,
        temperature=cfg.openai_temperature,
    )
