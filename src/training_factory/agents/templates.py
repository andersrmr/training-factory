import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "templates.schema.json"


def generate_templates(slides: dict[str, Any]) -> dict[str, Any]:
    deck = slides.get("deck", [])
    slide_count = len(deck)

    fallback = {
        "README.md": (
            "# Training Bundle\n\n"
            f"This training bundle contains {slide_count} slide(s) and related assets.\n"
        ),
        "RUNBOOK.md": (
            "# Runbook\n\n"
            "1. Review the brief and curriculum.\n"
            "2. Walk through slides and labs.\n"
            "3. Use QA checks to validate delivery readiness.\n"
        ),
    }
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce templates with keys README.md and RUNBOOK.md (both non-empty markdown strings). "
        f"Slides: {json.dumps(slides)}"
    )

    def _normalize(payload: dict) -> dict:
        if "templates" in payload and isinstance(payload["templates"], dict):
            payload = payload["templates"]
        return {
            "README.md": payload.get("README.md", fallback["README.md"]),
            "RUNBOOK.md": payload.get("RUNBOOK.md", fallback["RUNBOOK.md"]),
        }

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
