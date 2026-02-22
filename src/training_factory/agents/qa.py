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
    if filename == "README.md":
        node = templates.get("readme_md")
    elif filename == "RUNBOOK.md":
        node = templates.get("runbook_md")
    else:
        node = None

    if isinstance(node, dict) and isinstance(node.get("content"), str):
        return node["content"]

    direct = templates.get(filename)
    if isinstance(direct, str):
        return direct
    return ""


def _slide_text(slides: dict[str, Any]) -> str:
    deck = slides.get("deck")
    if not isinstance(deck, list):
        return ""

    parts: list[str] = []
    for item in deck:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        if isinstance(title, str):
            parts.append(title)
        bullets = item.get("bullets")
        if isinstance(bullets, list):
            parts.extend([b for b in bullets if isinstance(b, str)])
    return " ".join(parts).strip()


def _slides_reference_lab(slides: dict[str, Any]) -> bool:
    text = _slide_text(slides).lower()
    if not text:
        return False
    return any(token in text for token in ("lab", "exercise", "hands-on", "checkpoint"))


def _templates_align_with_materials(slides: dict[str, Any], lab: dict[str, Any], templates: dict[str, Any]) -> bool:
    readme = _template_content(templates, "README.md").lower()
    runbook = _template_content(templates, "RUNBOOK.md").lower()
    slide_text = _slide_text(slides).lower()

    lab_present = bool(lab)
    slides_present = bool(slide_text)
    templates_present = bool(readme) and bool(runbook)
    if not (lab_present and slides_present and templates_present):
        return False

    combined = f"{readme} {runbook}"
    has_lab_ref = any(token in combined for token in ("lab", "exercise", "checkpoint"))
    has_slide_ref = any(token in combined for token in ("slide", "deck", "module", "lesson"))
    return has_lab_ref and has_slide_ref


def _is_plausible_markdown(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) >= 20 and ("\n" in stripped or stripped.startswith("#"))


def _research_ids(research: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    sources = research.get("sources", [])
    if not isinstance(sources, list):
        return ids
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id = source.get("id")
        if isinstance(source_id, str) and source_id.strip():
            ids.add(source_id.strip())
    return ids


def _curriculum_references_valid(curriculum: dict[str, Any], valid_ids: set[str]) -> bool:
    references_used = curriculum.get("references_used")
    if not isinstance(references_used, list) or not references_used:
        return False
    for item in references_used:
        if not isinstance(item, str) or not item.strip() or item.strip() not in valid_ids:
            return False
    return True


def _module_sources_valid(curriculum: dict[str, Any], valid_ids: set[str]) -> bool:
    modules = curriculum.get("modules")
    if not isinstance(modules, list) or not modules:
        return False
    for module in modules:
        if not isinstance(module, dict):
            return False
        sources = module.get("sources")
        if not isinstance(sources, list) or not sources:
            return False
        for source_id in sources:
            if not isinstance(source_id, str) or not source_id.strip() or source_id.strip() not in valid_ids:
                return False
    return True


def _source_tiers(research: dict[str, Any]) -> dict[str, str]:
    tiers: dict[str, str] = {}
    sources = research.get("sources", [])
    if not isinstance(sources, list):
        return tiers
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id = source.get("id")
        authority_tier = source.get("authority_tier")
        if isinstance(source_id, str) and source_id.strip() and isinstance(authority_tier, str):
            tiers[source_id.strip()] = authority_tier.strip().upper()
    return tiers


def _is_sensitive_topic(topic: str) -> bool:
    lowered = topic.lower()
    return any(
        token in lowered
        for token in ("governance", "security", "risk", "compliance", "policy", "alm", "lifecycle")
    )


def _authority_usage_valid(curriculum: dict[str, Any], research: dict[str, Any]) -> bool:
    references_used = curriculum.get("references_used")
    if not isinstance(references_used, list) or not references_used:
        return False

    tiers_by_source = _source_tiers(research)
    cited_tiers: list[str] = []
    for source_id in references_used:
        if not isinstance(source_id, str) or not source_id.strip():
            continue
        tier = tiers_by_source.get(source_id.strip())
        if not tier:
            continue
        cited_tiers.append(tier)

    topic = str(curriculum.get("topic", ""))
    sensitive_topic = _is_sensitive_topic(topic)
    tier_a_count = sum(1 for tier in cited_tiers if tier == "A")
    tier_b_count = sum(1 for tier in cited_tiers if tier == "B")

    if sensitive_topic:
        return tier_a_count >= 1
    return tier_a_count >= 1 or tier_b_count >= 2


def generate_qa(
    slides: dict[str, Any],
    lab: dict[str, Any],
    templates: dict[str, Any],
    curriculum: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    lab_has_structure = _has_steps_and_checkpoints(lab)
    slides_have_content = bool(_slide_text(slides))
    slides_reference_lab = _slides_reference_lab(slides)
    has_readme = bool(_template_content(templates, "README.md"))
    has_runbook = bool(_template_content(templates, "RUNBOOK.md"))
    templates_align = _templates_align_with_materials(slides, lab, templates)
    research_ids = _research_ids(research)
    has_valid_curriculum_refs = _curriculum_references_valid(curriculum, research_ids)
    has_valid_module_sources = _module_sources_valid(curriculum, research_ids)
    has_authoritative_citations = _authority_usage_valid(curriculum, research)

    checks = [
        {
            "prompt": "Do slides align with curriculum/lab objectives?",
            "answer": "Yes" if slides_have_content and lab_has_structure else "No",
        },
        {
            "prompt": "Do slides reference the lab appropriately?",
            "answer": "Yes" if slides_reference_lab else "No",
        },
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
        {
            "prompt": "Do templates align with slides and lab?",
            "answer": "Yes" if templates_align else "No",
        },
        {
            "prompt": "Does curriculum include references_used and are they valid research source IDs?",
            "answer": "Yes" if has_valid_curriculum_refs else "No",
        },
        {
            "prompt": "Does each curriculum module include sources and are they valid research source IDs?",
            "answer": "Yes" if has_valid_module_sources else "No",
        },
        {
            "prompt": "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?",
            "answer": "Yes" if has_authoritative_citations else "No",
        },
    ]

    status = "pass" if all(item["answer"] == "Yes" for item in checks) else "fail"
    fallback = {"status": status, "checks": checks}
    offline_templates_ok = _is_plausible_markdown(_template_content(templates, "README.md")) and _is_plausible_markdown(
        _template_content(templates, "RUNBOOK.md")
    )
    offline_stub = {
        "status": (
            "pass"
            if (
                offline_templates_ok
                and has_valid_curriculum_refs
                and has_valid_module_sources
                and has_authoritative_citations
            )
            else "fail"
        ),
        "checks": [
            {
                "prompt": "Do templates include non-empty plausible README.md content?",
                "answer": "Yes" if _is_plausible_markdown(_template_content(templates, "README.md")) else "No",
            },
            {
                "prompt": "Do templates include non-empty plausible RUNBOOK.md content?",
                "answer": "Yes" if _is_plausible_markdown(_template_content(templates, "RUNBOOK.md")) else "No",
            },
            {
                "prompt": "Does curriculum include references_used and are they valid research source IDs?",
                "answer": "Yes" if has_valid_curriculum_refs else "No",
            },
            {
                "prompt": "Does each curriculum module include sources and are they valid research source IDs?",
                "answer": "Yes" if has_valid_module_sources else "No",
            },
            {
                "prompt": "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?",
                "answer": "Yes" if has_authoritative_citations else "No",
            },
        ],
    }
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce QA with keys status and checks. "
        "status must be pass or fail. checks is an array of {prompt, answer}. "
        "Checks must include: "
        "(1) slides align with curriculum/lab objectives using slide titles/bullets, "
        "(2) slides reference the lab appropriately at least conceptually, "
        "(3) lab exists and has steps/checkpoints, "
        "(4) templates includes README.md, "
        "(5) templates includes RUNBOOK.md, "
        "(6) templates align with slides and lab (README + RUNBOOK consistent), "
        "(7) curriculum references_used exists and cites valid research source IDs, "
        "(8) each curriculum module includes sources with valid research source IDs, "
        "(9) curriculum cites sufficiently authoritative Tier A/B sources based on topic sensitivity. "
        f"Slides: {json.dumps(slides)}. Lab: {json.dumps(lab)}. Templates: {json.dumps(templates)}. "
        f"Curriculum: {json.dumps(curriculum)}. Research: {json.dumps(research)}"
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
        offline_stub=offline_stub,
    )
