from __future__ import annotations

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


def _coerce_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return str(content)


def invoke_text(prompt: str, fallback_text: str) -> str:
    """Invoke the LLM and return text content, falling back for local runs."""

    settings = get_settings()
    if not settings.openai_api_key:
        return fallback_text

    model = build_chat_model(settings)
    response = model.invoke(prompt)
    return _coerce_content_to_text(response.content)
