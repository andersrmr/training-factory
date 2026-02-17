import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "slides.schema.json"


def _module_bullets(title: str) -> list[str]:
    return [
        f"Learning objective: explain and apply core ideas from {title}.",
        f"Concept 1: key terminology and foundational principles for {title}.",
        f"Concept 2: workflow, decisions, and tradeoffs when using {title}.",
        f"Practical example: a short real-world use case that demonstrates {title} in action.",
    ]


def generate_slides(curriculum: dict[str, Any]) -> dict[str, Any]:
    modules = curriculum.get("modules", [])
    deck = []
    for idx, module in enumerate(modules, start=1):
        module_title = module.get("title", f"Module {idx}")
        deck.append(
            {
                "slide": idx,
                "title": module_title,
                "bullets": _module_bullets(module_title),
            }
        )

    fallback = {"deck": deck}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce slides with key deck, where each item has "
        "slide, title, bullets. "
        "For each slide, generate exactly 4 bullets in this order: "
        "(1) one learning objective specific to the module title, "
        "(2) one concrete concept, "
        "(3) one concrete concept, "
        "(4) one short practical example or use case. "
        "Do not use placeholders like 'Learning objective', 'Core concept', or 'Example'; "
        "derive all bullet text from the module title. "
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
