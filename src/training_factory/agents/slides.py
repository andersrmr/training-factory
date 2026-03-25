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
        f"Hands-on lab checkpoint: complete a short exercise for {title} and verify the expected outcome.",
    ]


def _has_lab_language(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("lab", "exercise", "hands-on", "checkpoint"))


def _normalize_slide_item(item: Any, index: int) -> dict[str, Any]:
    title = f"Module {index}"
    if isinstance(item, dict) and isinstance(item.get("title"), str) and item.get("title", "").strip():
        title = item["title"].strip()

    bullets = _module_bullets(title)
    if isinstance(item, dict) and isinstance(item.get("bullets"), list):
        candidate_bullets = [bullet.strip() for bullet in item["bullets"] if isinstance(bullet, str) and bullet.strip()]
        if candidate_bullets:
            bullets = candidate_bullets[:4]

    while len(bullets) < 4:
        bullets.append(_module_bullets(title)[len(bullets)])

    combined_text = " ".join([title] + bullets)
    if not _has_lab_language(combined_text):
        bullets[-1] = f"Hands-on lab checkpoint: complete a short exercise for {title} and verify the expected outcome."

    return {"slide": index, "title": title, "bullets": bullets[:4]}


def generate_slides(curriculum: dict[str, Any], *, retry_strategy: dict[str, Any] | None = None) -> dict[str, Any]:
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
    strategy = retry_strategy or {}
    failed_checks = {
        str(item).strip()
        for item in strategy.get("failed_checks", [])
        if isinstance(item, str) and str(item).strip()
    }
    retry_guidance = ""
    if "slides_alignment" in failed_checks:
        retry_guidance += (
            " Strengthen slide-to-curriculum alignment by making each title and bullet explicitly reflect the "
            "module goal and cited topic."
        )
    if "slides_reference_lab" in failed_checks:
        retry_guidance += (
            " Ensure slide bullets explicitly mention the associated hands-on lab, exercise, or checkpoint when relevant."
        )
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce slides with key deck, where each item has "
        "slide, title, bullets. "
        "For each slide, generate exactly 4 bullets in this order: "
        "(1) one learning objective specific to the module title, "
        "(2) one concrete concept, "
        "(3) one concrete concept, "
        "(4) one hands-on lab, exercise, or checkpoint reference tied to the module title. "
        "Do not use placeholders like 'Learning objective', 'Core concept', or 'Example'; "
        "derive all bullet text from the module title. "
        f"{retry_guidance} "
        f"Curriculum: {json.dumps(curriculum)}"
    )

    def _normalize(payload: dict) -> dict:
        if "slides" in payload and isinstance(payload["slides"], dict):
            payload = payload["slides"]
        deck_payload = payload.get("deck", fallback["deck"])
        if not isinstance(deck_payload, list):
            deck_payload = fallback["deck"]
        normalized_deck = [_normalize_slide_item(item, index) for index, item in enumerate(deck_payload, start=1)]
        return {"deck": normalized_deck or fallback["deck"]}

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
