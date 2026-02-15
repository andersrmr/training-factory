import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.json_extract import extract_json_object
from training_factory.utils.json_schema import validate_json

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "slides.schema.json"


def generate_slides(curriculum: dict[str, Any]) -> dict[str, Any]:
    modules = curriculum.get("modules", [])
    deck = []
    for idx, module in enumerate(modules, start=1):
        deck.append(
            {
                "slide": idx,
                "title": module.get("title", f"Module {idx}"),
                "bullets": ["Learning objective", "Core concept", "Example"],
            }
        )

    fallback = {"deck": deck}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce slides with key deck, where each item has "
        "slide, title, bullets. "
        f"Curriculum: {json.dumps(curriculum)}"
    )
    raw = llm.invoke_text(prompt=prompt, fallback_text=json.dumps(fallback))
    payload = extract_json_object(raw)
    if "slides" in payload and isinstance(payload["slides"], dict):
        payload = payload["slides"]

    slides = {"deck": payload.get("deck", fallback["deck"])}
    validate_json(slides, SCHEMA_PATH)
    return slides
