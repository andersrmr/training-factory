import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

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

    def _normalize(payload: dict) -> dict:
        if "curriculum" in payload and isinstance(payload["curriculum"], dict):
            payload = payload["curriculum"]
        return {"modules": payload.get("modules", fallback["modules"])}

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
