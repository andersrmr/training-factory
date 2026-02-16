import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

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

    def _normalize(payload: dict) -> dict:
        if "slides" in payload and isinstance(payload["slides"], dict):
            payload = payload["slides"]
        return {"deck": payload.get("deck", fallback["deck"])}

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
