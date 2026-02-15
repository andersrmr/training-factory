import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.json_schema import validate_json

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
        "Return only JSON for a training brief with keys: "
        "topic, audience, goals (string array), constraints (string array). "
        f"Topic: {topic}. Audience: {audience}."
    )
    raw = llm.invoke_text(prompt=prompt, fallback_text=json.dumps(fallback))
    brief = llm.parse_json_object(raw)
    validate_json(brief, SCHEMA_PATH)
    return brief
