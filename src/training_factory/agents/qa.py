import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "qa.schema.json"


def _has_steps_and_checkpoints(lab: dict[str, Any]) -> bool:
    if isinstance(lab.get("steps"), list) and lab.get("steps") and isinstance(lab.get("checkpoints"), list) and lab.get("checkpoints"):
        return True

    labs = lab.get("labs")
    if isinstance(labs, list):
        for item in labs:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("steps"), list) and item.get("steps") and isinstance(item.get("checkpoints"), list) and item.get("checkpoints"):
                return True
    return False


def _template_content(templates: dict[str, Any], filename: str) -> str:
    direct = templates.get(filename)
    if isinstance(direct, str):
        return direct

    if filename == "README.md":
        node = templates.get("readme_md")
    elif filename == "RUNBOOK.md":
        node = templates.get("runbook_md")
    else:
        node = None

    if isinstance(node, dict):
        if node.get("filename") == filename and isinstance(node.get("content"), str):
            return node["content"]
    return ""


def generate_qa(lab: dict[str, Any], templates: dict[str, Any]) -> dict[str, Any]:
    lab_has_structure = _has_steps_and_checkpoints(lab)
    has_readme = bool(_template_content(templates, "README.md"))
    has_runbook = bool(_template_content(templates, "RUNBOOK.md"))

    checks = [
        {
            "prompt": "Does lab exist and include steps/checkpoints?",
            "answer": "Yes" if lab_has_structure else "No",
        },
        {
            "prompt": "Does templates include README.md?",
            "answer": "Yes" if has_readme else "No",
        },
        {
            "prompt": "Does templates include RUNBOOK.md?",
            "answer": "Yes" if has_runbook else "No",
        },
    ]

    status = "pass" if all(item["answer"] == "Yes" for item in checks) else "fail"
    fallback = {"status": status, "checks": checks}
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce QA with keys status and checks. "
        "status must be pass or fail. checks is an array of {prompt, answer}. "
        "Checks must include: "
        "(1) lab exists and has steps/checkpoints, "
        "(2) templates includes README.md, "
        "(3) templates includes RUNBOOK.md. "
        f"Lab: {json.dumps(lab)}. Templates: {json.dumps(templates)}"
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
