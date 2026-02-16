import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "qa.schema.json"


def generate_qa(slides: dict[str, Any]) -> dict[str, Any]:
    deck = slides.get("deck", [])
    checks = []
    for slide in deck:
        title = slide.get("title", "Unknown")
        checks.append({"prompt": f"What is one key idea from '{title}'?", "answer": "Sample answer"})

    fallback = {"status": "pass", "checks": checks}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce QA with keys status and checks. "
        "status must be pass or fail. checks is an array of {prompt, answer}. "
        f"Slides: {json.dumps(slides)}"
    )

    def _normalize(payload: dict) -> dict:
        if "qa" in payload and isinstance(payload["qa"], dict):
            payload = payload["qa"]
        return {
            "status": payload.get("status", fallback["status"]),
            "checks": payload.get("checks", fallback["checks"]),
        }

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
