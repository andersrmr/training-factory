import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.json_schema import validate_json

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "qa.schema.json"


def generate_qa(slides: dict[str, Any]) -> dict[str, Any]:
    deck = slides.get("deck", [])
    checks = []
    for slide in deck:
        title = slide.get("title", "Unknown")
        checks.append({"prompt": f"What is one key idea from '{title}'?", "answer": "Sample answer"})

    fallback = {"status": "pass", "checks": checks}
    prompt = (
        "Return only JSON for QA with keys status and checks. "
        "status must be pass or fail. checks is an array of {prompt, answer}. "
        f"Slides: {json.dumps(slides)}"
    )
    raw = llm.invoke_text(prompt=prompt, fallback_text=json.dumps(fallback))
    qa = llm.parse_json_object(raw)
    validate_json(qa, SCHEMA_PATH)
    return qa
