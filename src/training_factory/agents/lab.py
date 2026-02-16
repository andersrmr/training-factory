import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "lab.schema.json"


def generate_lab(curriculum: dict[str, Any]) -> dict[str, Any]:
    modules = curriculum.get("modules", [])
    labs = []
    for idx, module in enumerate(modules, start=1):
        title = module.get("title", f"Module {idx}")
        labs.append(
            {
                "title": f"Lab: {title}",
                "instructions": [
                    f"Complete a practical exercise for {title}",
                    "Share your approach and reasoning",
                ],
                "expected_outcome": f"Learner can apply concepts from {title}",
            }
        )

    fallback = {"labs": labs}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce lab activities with key labs. "
        "Each lab must include title, instructions (string array), and expected_outcome. "
        f"Curriculum: {json.dumps(curriculum)}"
    )

    def _normalize(payload: dict) -> dict:
        if "lab" in payload and isinstance(payload["lab"], dict):
            payload = payload["lab"]
        if "labs" in payload and isinstance(payload["labs"], list):
            return {"labs": payload["labs"]}
        return fallback

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
