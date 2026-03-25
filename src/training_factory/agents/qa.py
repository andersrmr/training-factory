from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "qa.schema.json"

_SLIDES_ALIGN_PROMPT = "Do slides align with curriculum/lab objectives?"
_SLIDES_REFERENCE_LAB_PROMPT = "Do slides reference the lab appropriately?"
_LAB_STRUCTURE_PROMPT = "Does lab exist and include steps/checkpoints?"
_README_PROMPT = "Does templates include README.md?"
_RUNBOOK_PROMPT = "Does templates include RUNBOOK.md?"
_TEMPLATES_ALIGN_PROMPT = "Do templates align with slides and lab?"
_CURRICULUM_REFS_PROMPT = "Does curriculum include references_used and are they valid research source IDs?"
_MODULE_SOURCES_PROMPT = "Does each curriculum module include sources and are they valid research source IDs?"
_AUTHORITY_PROMPT = "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?"


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


def _meaningful_tokens(text: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return {token for token in normalized.split() if len(token) > 3}


def _slides_align_with_curriculum(slides: dict[str, Any], curriculum: dict[str, Any]) -> bool:
    deck = slides.get("deck")
    modules = curriculum.get("modules")
    if not isinstance(deck, list) or not deck:
        return False
    if not isinstance(modules, list) or not modules:
        return False
    if len(deck) < len(modules):
        return False

    for module, slide in zip(modules, deck):
        if not isinstance(module, dict) or not isinstance(slide, dict):
            return False

        module_title = str(module.get("title", "")).strip()
        slide_title = str(slide.get("title", "")).strip()
        bullets = slide.get("bullets")
        if not module_title or not slide_title or not isinstance(bullets, list) or not bullets:
            return False

        module_tokens = _meaningful_tokens(module_title)
        slide_title_tokens = _meaningful_tokens(slide_title)
        slide_text_tokens = _meaningful_tokens(
            " ".join(
                [slide_title]
                + [item for item in bullets if isinstance(item, str)]
            )
        )
        if not module_tokens:
            return False

        title_overlap = module_tokens & slide_title_tokens
        text_overlap = module_tokens & slide_text_tokens
        min_overlap = 1 if len(module_tokens) == 1 else 2
        if len(title_overlap) < min_overlap or len(text_overlap) < min_overlap:
            return False

    return True


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
    slide_titles = slides.get("deck")
    title_token_overlap = False
    if isinstance(slide_titles, list):
        template_tokens = set(combined.replace("-", " ").split())
        for item in slide_titles:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip().lower()
            if not title:
                continue
            title_tokens = {
                token
                for token in "".join(ch if ch.isalnum() else " " for ch in title).split()
                if len(token) > 3
            }
            if title_tokens and title_tokens & template_tokens:
                title_token_overlap = True
                break
    return has_lab_ref and has_slide_ref and title_token_overlap


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


def _build_deterministic_checks(
    *,
    lab_has_structure: bool,
    slides_have_content: bool,
    slides_reference_lab: bool,
    has_readme: bool,
    has_runbook: bool,
    templates_align: bool,
    has_valid_curriculum_refs: bool,
    has_valid_module_sources: bool,
    has_authoritative_citations: bool,
) -> list[dict[str, str]]:
    return [
        {
            "prompt": _SLIDES_ALIGN_PROMPT,
            "answer": "Yes" if slides_have_content and lab_has_structure else "No",
        },
        {
            "prompt": _SLIDES_REFERENCE_LAB_PROMPT,
            "answer": "Yes" if slides_reference_lab else "No",
        },
        {
            "prompt": _LAB_STRUCTURE_PROMPT,
            "answer": "Yes" if lab_has_structure else "No",
        },
        {
            "prompt": _README_PROMPT,
            "answer": "Yes" if has_readme else "No",
        },
        {
            "prompt": _RUNBOOK_PROMPT,
            "answer": "Yes" if has_runbook else "No",
        },
        {
            "prompt": _TEMPLATES_ALIGN_PROMPT,
            "answer": "Yes" if templates_align else "No",
        },
        {
            "prompt": _CURRICULUM_REFS_PROMPT,
            "answer": "Yes" if has_valid_curriculum_refs else "No",
        },
        {
            "prompt": _MODULE_SOURCES_PROMPT,
            "answer": "Yes" if has_valid_module_sources else "No",
        },
        {
            "prompt": _AUTHORITY_PROMPT,
            "answer": "Yes" if has_authoritative_citations else "No",
        },
    ]


def generate_qa(
    slides: dict[str, Any],
    lab: dict[str, Any],
    templates: dict[str, Any],
    curriculum: dict[str, Any],
    research: dict[str, Any],
) -> dict[str, Any]:
    lab_has_structure = _has_steps_and_checkpoints(lab)
    slides_have_content = _slide_text(slides)
    slides_align = _slides_align_with_curriculum(slides, curriculum)
    slides_reference_lab = _slides_reference_lab(slides)
    has_readme = bool(_template_content(templates, "README.md"))
    has_runbook = bool(_template_content(templates, "RUNBOOK.md"))
    templates_align = _templates_align_with_materials(slides, lab, templates)
    research_ids = _research_ids(research)
    has_valid_curriculum_refs = _curriculum_references_valid(curriculum, research_ids)
    has_valid_module_sources = _module_sources_valid(curriculum, research_ids)
    has_authoritative_citations = _authority_usage_valid(curriculum, research)

    deterministic_checks = _build_deterministic_checks(
        lab_has_structure=lab_has_structure,
        slides_have_content=slides_align,
        slides_reference_lab=slides_reference_lab,
        has_readme=has_readme,
        has_runbook=has_runbook,
        templates_align=templates_align,
        has_valid_curriculum_refs=has_valid_curriculum_refs,
        has_valid_module_sources=has_valid_module_sources,
        has_authoritative_citations=has_authoritative_citations,
    )
    status = "pass" if all(item["answer"] == "Yes" for item in deterministic_checks) else "fail"
    return {"status": status, "checks": deterministic_checks}
