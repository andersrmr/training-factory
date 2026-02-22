import json
from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "curriculum.schema.json"


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def generate_curriculum(brief: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    topic = brief.get("topic", "Untitled Topic")
    audience = brief.get("audience", "general")
    research_sources = research.get("sources", []) if isinstance(research, dict) else []
    valid_source_ids = [
        str(source.get("id")).strip()
        for source in research_sources
        if isinstance(source, dict) and str(source.get("id", "")).strip()
    ]
    fallback_source_ids = valid_source_ids[:2] if valid_source_ids else ["src_001"]
    source_listing = []
    for source in research_sources[:12]:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("id", "")).strip()
        source_title = str(source.get("title", "")).strip()
        if source_id:
            source_listing.append({"id": source_id, "title": source_title})

    fallback = {
        "topic": topic,
        "audience": audience,
        "modules": [
            {
                "title": f"{topic}: Foundations",
                "duration_minutes": 30,
                "sources": fallback_source_ids[:1],
            },
            {
                "title": f"{topic}: Practice",
                "duration_minutes": 30,
                "sources": fallback_source_ids[:1],
            },
        ],
        "references_used": fallback_source_ids,
    }
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce a training curriculum with keys: topic, audience, modules, references_used. "
        "modules must be an array of objects that include at least title, duration_minutes, and sources. "
        "references_used must be a non-empty array of source ids. "
        "Each module.sources must be non-empty and use only source ids present in the allowed id list. "
        "Do not invent source ids. "
        f"Allowed source ids: {', '.join(valid_source_ids) if valid_source_ids else 'src_001'}. "
        f"Brief JSON: {json.dumps(brief)} "
        f"Research source listing: {json.dumps(source_listing)}"
    )

    def _normalize(payload: dict) -> dict:
        if "curriculum" in payload and isinstance(payload["curriculum"], dict):
            payload = payload["curriculum"]
        references_used = [
            source_id
            for source_id in _as_string_list(payload.get("references_used"))
            if source_id in valid_source_ids
        ]
        if not references_used:
            references_used = list(fallback_source_ids)

        normalized_modules: list[dict[str, Any]] = []
        raw_modules = payload.get("modules")
        if isinstance(raw_modules, list):
            for module in raw_modules:
                if not isinstance(module, dict):
                    continue
                source_ids = [
                    source_id
                    for source_id in _as_string_list(module.get("sources"))
                    if source_id in valid_source_ids
                ]
                if not source_ids:
                    source_ids = references_used[:1]
                normalized_module = dict(module)
                normalized_module["sources"] = source_ids
                normalized_modules.append(normalized_module)
        if not normalized_modules:
            normalized_modules = list(fallback["modules"])

        return {
            "topic": str(payload.get("topic", fallback["topic"])),
            "audience": str(payload.get("audience", fallback["audience"])),
            "modules": normalized_modules,
            "references_used": references_used,
        }

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
