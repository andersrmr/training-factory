import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "qa.schema.json"


def generate_qa(templates: dict[str, Any]) -> dict[str, Any]:
    readme_text = templates.get("README.md", "")
    runbook_text = templates.get("RUNBOOK.md", "")
    checks_source = [("README.md", readme_text), ("RUNBOOK.md", runbook_text)]
    checks = []
    for name, content in checks_source:
        checks.append(
            {
                "prompt": f"Does {name} include actionable guidance?",
                "answer": "Yes" if content else "No",
            }
        )

    fallback = {"status": "pass", "checks": checks}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce QA with keys status and checks. "
        "status must be pass or fail. checks is an array of {prompt, answer}. "
        f"Templates: {json.dumps(templates)}"
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
