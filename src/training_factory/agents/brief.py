from pathlib import Path
from typing import Any

from training_factory import llm
from training_factory.utils.structured_output import generate_structured_output

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "brief.schema.json"


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def generate_brief(request: dict[str, Any], research: dict[str, Any]) -> dict[str, Any]:
    topic = request.get("topic", "Untitled Topic")
    audience = request.get("audience", "general")
    research_sources = research.get("sources", []) if isinstance(research, dict) else []
    valid_source_ids = [
        str(item.get("id")).strip()
        for item in research_sources
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    ]
    fallback_source_ids = valid_source_ids[:2] if valid_source_ids else ["src_001"]
    default_guideline_source = fallback_source_ids[:1]
    context_pack = str(research.get("context_pack", "")) if isinstance(research, dict) else ""
    context_pack = context_pack[:4000]

    fallback = {
        "topic": topic,
        "audience": audience,
        "goals": [f"Understand fundamentals of {topic}"],
        "constraints": ["Keep explanations clear and concise"],
        "references_used": fallback_source_ids,
        "key_guidelines": [
            {
                "guideline": "Ground recommendations in official guidance and practical constraints.",
                "rationale": "Stable, authoritative guidance reduces implementation risk for novices.",
                "sources": default_guideline_source,
            }
        ],
    }
    ids_text = ", ".join(valid_source_ids) if valid_source_ids else "src_001"
    prompt = (
        "Return JSON only. Do not include markdown fences, labels, or extra prose. "
        "Produce a training brief with keys: "
        "topic, audience, goals (string array), constraints (string array), "
        "references_used (string array), key_guidelines (array of objects with "
        "guideline, rationale, sources string array). "
        "Every key_guideline.sources must include at least one source id from the "
        "allowed list. Do not invent source ids. If evidence is sparse, use the available ids. "
        f"Allowed source ids: {ids_text}. "
        f"Topic: {topic}. Audience: {audience}. "
        f"Research context:\n{context_pack}"
    )

    def _normalize(payload: dict) -> dict:
        if "brief" in payload and isinstance(payload["brief"], dict):
            payload = payload["brief"]
        references_used = [
            source_id
            for source_id in _as_string_list(payload.get("references_used"))
            if source_id in valid_source_ids
        ]
        if not references_used:
            references_used = list(fallback_source_ids)

        normalized_guidelines: list[dict[str, Any]] = []
        raw_guidelines = payload.get("key_guidelines", [])
        if isinstance(raw_guidelines, list):
            for guideline in raw_guidelines:
                if not isinstance(guideline, dict):
                    continue
                guideline_text = str(guideline.get("guideline", "")).strip()
                rationale_text = str(guideline.get("rationale", "")).strip()
                sources = [
                    source_id
                    for source_id in _as_string_list(guideline.get("sources"))
                    if source_id in valid_source_ids
                ]
                if not sources:
                    sources = references_used[:1]
                if guideline_text and rationale_text:
                    normalized_guidelines.append(
                        {
                            "guideline": guideline_text,
                            "rationale": rationale_text,
                            "sources": sources,
                        }
                    )

        if not normalized_guidelines:
            normalized_guidelines = list(fallback["key_guidelines"])

        goals = _as_string_list(payload.get("goals"))
        constraints = _as_string_list(payload.get("constraints"))
        return {
            "topic": payload.get("topic", fallback["topic"]),
            "audience": payload.get("audience", fallback["audience"]),
            "goals": goals or fallback["goals"],
            "constraints": constraints or fallback["constraints"],
            "references_used": references_used,
            "key_guidelines": normalized_guidelines,
        }

    return generate_structured_output(
        model=llm,
        prompt=prompt,
        schema_path=SCHEMA_PATH,
        normalize=_normalize,
        offline_stub=fallback,
    )
