import json
from pathlib import Path
from typing import Any

from training_factory import llm
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
        "Return only JSON for slides with key deck, where each item has "
        "slide, title, bullets. "
        f"Curriculum: {json.dumps(curriculum)}"
    )
    raw = llm.invoke_text(prompt=prompt, fallback_text=json.dumps(fallback))
    slides = llm.parse_json_object(raw)
    validate_json(slides, SCHEMA_PATH)
    return slides
