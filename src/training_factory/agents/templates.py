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


def _slide_titles(slides: dict[str, Any]) -> list[str]:
    deck = slides.get("deck", [])
    if not isinstance(deck, list):
        return []

    titles: list[str] = []
    for item in deck:
        if isinstance(item, dict) and isinstance(item.get("title"), str) and item.get("title", "").strip():
            titles.append(item["title"].strip())
    return titles


def _joined_slide_titles(slides: dict[str, Any]) -> str:
    titles = _slide_titles(slides)
    return ", ".join(titles) if titles else "the module topics"


def _legacy_fallback(slides: dict[str, Any]) -> dict[str, str]:
    title_text = _joined_slide_titles(slides)
    return {
        "README.md": (
            "# Training Bundle\n\n"
            f"This training bundle uses the slide deck and module flow for {title_text}. "
            "Learners should complete the hands-on lab exercise and checkpoint review for each module.\n"
        ),
        "RUNBOOK.md": (
            "# Runbook\n\n"
            f"1. Review the slide deck for {title_text} and confirm the module sequence.\n"
            "2. Walk through the hands-on lab exercise and checkpoint review for each module.\n"
            "3. Use QA checks to validate delivery readiness.\n"
        ),
    }


def _structured_fallback(legacy: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
        "readme_md": {"filename": "README.md", "content": legacy["README.md"]},
        "runbook_md": {"filename": "RUNBOOK.md", "content": legacy["RUNBOOK.md"]},
    }


def _normalize_document_node(
    node: Any,
    *,
    expected_filename: str,
    fallback: dict[str, str],
) -> dict[str, str]:
    if not isinstance(node, dict):
        return fallback

    filename = node.get("filename", expected_filename)
    content = node.get("content")
    if not isinstance(filename, str):
        filename = expected_filename
    if not isinstance(content, str):
        return fallback

    return {"filename": filename, "content": content}


def _legacy_to_structured(payload: dict[str, Any], fallback: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    readme = payload.get("README.md", fallback["readme_md"]["content"])
    runbook = payload.get("RUNBOOK.md", fallback["runbook_md"]["content"])
    if not isinstance(readme, str):
        readme = fallback["readme_md"]["content"]
    if not isinstance(runbook, str):
        runbook = fallback["runbook_md"]["content"]
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
        candidate = readme.get("content", readme_content)
        if isinstance(candidate, str):
            readme_content = candidate
    if isinstance(runbook, dict):
        candidate = runbook.get("content", runbook_content)
        if isinstance(candidate, str):
            runbook_content = candidate

    return {"README.md": readme_content, "RUNBOOK.md": runbook_content}


def _ensure_template_alignment(
    content: str,
    *,
    fallback_content: str,
    slide_titles: list[str],
    document_name: str,
) -> str:
    text = content.strip() if isinstance(content, str) else ""
    if not text:
        text = fallback_content

    lowered = text.lower()
    has_lab_ref = any(token in lowered for token in ("lab", "exercise", "checkpoint"))
    has_slide_ref = any(token in lowered for token in ("slide", "deck", "module", "lesson"))
    has_title_ref = any(title.lower() in lowered for title in slide_titles if title.strip())

    if has_lab_ref and has_slide_ref and (has_title_ref or not slide_titles):
        return text

    title_text = ", ".join(slide_titles) if slide_titles else "the module topics"
    appendix = (
        f"\n\n{document_name} alignment notes: use the slide deck and module flow for {title_text}. "
        "Include the hands-on lab exercise and checkpoint review during delivery."
    )
    return f"{text}{appendix}".strip()


def generate_templates(slides: dict[str, Any], *, retry_strategy: dict[str, Any] | None = None) -> dict[str, Any]:
    slide_titles = _slide_titles(slides)
    strategy = retry_strategy or {}
    failed_checks = {
        str(item).strip()
        for item in strategy.get("failed_checks", [])
        if isinstance(item, str) and str(item).strip()
    }

    mode = _schema_mode()
    legacy_fallback = _legacy_fallback(slides)
    structured_fallback = _structured_fallback(legacy_fallback)
    fallback = structured_fallback if mode == "structured" else legacy_fallback
    retry_guidance = ""
    if "templates_alignment" in failed_checks:
        retry_guidance += (
            " Make README.md and RUNBOOK.md explicitly align with slide topics, module flow, and lab/checkpoint usage."
        )
    if "slides_reference_lab" in failed_checks:
        retry_guidance += " Explicitly mention the lab, exercise flow, and checkpoints in both template documents."

    if mode == "structured":
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce templates with keys readme_md and runbook_md. "
            "Each key must contain an object with filename and content. "
            "Filenames must be README.md and RUNBOOK.md. "
            f"{retry_guidance} "
            f"Slides: {json.dumps(slides)}"
        )
    else:
        prompt = (
            "Return JSON only. Do not include markdown fences, labels, or extra prose. "
            "Produce templates with keys README.md and RUNBOOK.md (both non-empty markdown strings). "
            f"{retry_guidance} "
            f"Slides: {json.dumps(slides)}"
        )

    def _normalize(payload: dict) -> dict:
        if "templates" in payload and isinstance(payload["templates"], dict):
            payload = payload["templates"]

        if mode == "structured":
            if "readme_md" in payload and "runbook_md" in payload:
                readme = payload.get("readme_md")
                runbook = payload.get("runbook_md")
                normalized = {
                    "readme_md": _normalize_document_node(
                        readme,
                        expected_filename="README.md",
                        fallback=structured_fallback["readme_md"],
                    ),
                    "runbook_md": _normalize_document_node(
                        runbook,
                        expected_filename="RUNBOOK.md",
                        fallback=structured_fallback["runbook_md"],
                    ),
                }
                normalized["readme_md"]["content"] = _ensure_template_alignment(
                    normalized["readme_md"]["content"],
                    fallback_content=structured_fallback["readme_md"]["content"],
                    slide_titles=slide_titles,
                    document_name="README",
                )
                normalized["runbook_md"]["content"] = _ensure_template_alignment(
                    normalized["runbook_md"]["content"],
                    fallback_content=structured_fallback["runbook_md"]["content"],
                    slide_titles=slide_titles,
                    document_name="RUNBOOK",
                )
                return normalized
            normalized = _legacy_to_structured(payload, structured_fallback)
            normalized["readme_md"]["content"] = _ensure_template_alignment(
                normalized["readme_md"]["content"],
                fallback_content=structured_fallback["readme_md"]["content"],
                slide_titles=slide_titles,
                document_name="README",
            )
            normalized["runbook_md"]["content"] = _ensure_template_alignment(
                normalized["runbook_md"]["content"],
                fallback_content=structured_fallback["runbook_md"]["content"],
                slide_titles=slide_titles,
                document_name="RUNBOOK",
            )
            return normalized

        if "README.md" in payload or "RUNBOOK.md" in payload:
            normalized = {
                "README.md": payload.get("README.md", legacy_fallback["README.md"]),
                "RUNBOOK.md": payload.get("RUNBOOK.md", legacy_fallback["RUNBOOK.md"]),
            }
            normalized["README.md"] = _ensure_template_alignment(
                normalized["README.md"],
                fallback_content=legacy_fallback["README.md"],
                slide_titles=slide_titles,
                document_name="README",
            )
            normalized["RUNBOOK.md"] = _ensure_template_alignment(
                normalized["RUNBOOK.md"],
                fallback_content=legacy_fallback["RUNBOOK.md"],
                slide_titles=slide_titles,
                document_name="RUNBOOK",
            )
            return normalized
        normalized = _structured_to_legacy(payload, legacy_fallback)
        normalized["README.md"] = _ensure_template_alignment(
            normalized["README.md"],
            fallback_content=legacy_fallback["README.md"],
            slide_titles=slide_titles,
            document_name="README",
        )
        normalized["RUNBOOK.md"] = _ensure_template_alignment(
            normalized["RUNBOOK.md"],
            fallback_content=legacy_fallback["RUNBOOK.md"],
            slide_titles=slide_titles,
            document_name="RUNBOOK",
        )
        return normalized

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
