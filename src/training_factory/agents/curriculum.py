import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.json_extract import extract_json_object
from training_factory.utils.json_schema import validate_json

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "curriculum.schema.json"


def generate_curriculum(brief: dict[str, Any]) -> dict[str, Any]:
    topic = brief.get("topic", "Untitled Topic")
    fallback = {
        "modules": [
            {"title": f"{topic}: Foundations", "duration_minutes": 30},
            {"title": f"{topic}: Practice", "duration_minutes": 30},
        ]
    }
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce a training curriculum with key modules, "
        "where modules is an array of {title, duration_minutes}. "
        f"Brief: {json.dumps(brief)}"
    )
    raw = llm.invoke_text(prompt=prompt, fallback_text=json.dumps(fallback))
    payload = extract_json_object(raw)
    if "curriculum" in payload and isinstance(payload["curriculum"], dict):
        payload = payload["curriculum"]

    curriculum = {"modules": payload.get("modules", fallback["modules"])}
    validate_json(curriculum, SCHEMA_PATH)
    return curriculum
