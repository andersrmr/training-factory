import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "templates.schema.json"


def _schema_mode() -> str:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    required = schema.get("required", [])
    if "README.md" in required:
        return "legacy"
    return "structured"


def _legacy_fallback(slide_count: int) -> dict[str, str]:
    return {
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


def _structured_fallback(legacy: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        "readme_md": {"filename": "README.md", "content": legacy["README.md"]},
        "runbook_md": {"filename": "RUNBOOK.md", "content": legacy["RUNBOOK.md"]},
    }


def _legacy_to_structured(payload: dict[str, Any], fallback: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    readme = payload.get("README.md", fallback["readme_md"]["content"])
    runbook = payload.get("RUNBOOK.md", fallback["runbook_md"]["content"])
    return {
        "readme_md": {"filename": "README.md", "content": readme},
        "runbook_md": {"filename": "RUNBOOK.md", "content": runbook},
    }


def _structured_to_legacy(payload: dict[str, Any], fallback: dict[str, str]) -> dict[str, str]:
    readme = payload.get("readme_md")
    runbook = payload.get("runbook_md")

    readme_content = fallback["README.md"]
    runbook_content = fallback["RUNBOOK.md"]

    if isinstance(readme, dict):
        readme_content = readme.get("content", readme_content)
    if isinstance(runbook, dict):
        runbook_content = runbook.get("content", runbook_content)

    return {"README.md": readme_content, "RUNBOOK.md": runbook_content}


def generate_templates(slides: dict[str, Any]) -> dict[str, Any]:
    deck = slides.get("deck", [])
    slide_count = len(deck)

    mode = _schema_mode()
    legacy_fallback = _legacy_fallback(slide_count)
    structured_fallback = _structured_fallback(legacy_fallback)
    fallback = structured_fallback if mode == "structured" else legacy_fallback

    if mode == "structured":
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce templates with keys readme_md and runbook_md. "
            "Each key must contain an object with filename and content. "
            "Filenames must be README.md and RUNBOOK.md. "
            f"Slides: {json.dumps(slides)}"
        )
    else:
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce templates with keys README.md and RUNBOOK.md (both non-empty markdown strings). "
            f"Slides: {json.dumps(slides)}"
        )

    def _normalize(payload: dict) -> dict:
        if "templates" in payload and isinstance(payload["templates"], dict):
            payload = payload["templates"]

        if mode == "structured":
            if "readme_md" in payload and "runbook_md" in payload:
                readme = payload.get("readme_md")
                runbook = payload.get("runbook_md")
                return {
                    "readme_md": readme if isinstance(readme, dict) else structured_fallback["readme_md"],
                    "runbook_md": runbook if isinstance(runbook, dict) else structured_fallback["runbook_md"],
                }
            return _legacy_to_structured(payload, structured_fallback)

        if "README.md" in payload or "RUNBOOK.md" in payload:
            return {
                "README.md": payload.get("README.md", legacy_fallback["README.md"]),
                "RUNBOOK.md": payload.get("RUNBOOK.md", legacy_fallback["RUNBOOK.md"]),
            }
        return _structured_to_legacy(payload, legacy_fallback)

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
