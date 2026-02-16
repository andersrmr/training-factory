from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "brief.schema.json"


def generate_brief(request: dict[str, Any]) -> dict[str, Any]:
    topic = request.get("topic", "Untitled Topic")
    audience = request.get("audience", "general")
    fallback = {
        "topic": topic,
        "audience": audience,
        "goals": [f"Understand fundamentals of {topic}"],
        "constraints": ["Keep explanations clear and concise"],
    }
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce a training brief with keys: "
        "topic, audience, goals (string array), constraints (string array). "
        f"Topic: {topic}. Audience: {audience}."
    )

    def _normalize(payload: dict) -> dict:
        if "brief" in payload and isinstance(payload["brief"], dict):
            payload = payload["brief"]
        return {
            "topic": payload.get("topic", fallback["topic"]),
            "audience": payload.get("audience", fallback["audience"]),
            "goals": payload.get("goals", fallback["goals"]),
            "constraints": payload.get("constraints", fallback["constraints"]),
        }

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
