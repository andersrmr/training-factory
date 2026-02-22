from __future__ import annotations

from pathlib import Path
from typing import Any

from training_factory.utils.json_schema import validate_json

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "research_qa.schema.json"


def _tokenize(value: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return {token for token in normalized.split() if len(token) > 2}


def generate_research_qa(research: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    sources = research.get("sources", []) if isinstance(research.get("sources"), list) else []
    query_plan = research.get("query_plan", {}) if isinstance(research.get("query_plan"), dict) else {}
    topic = str(request.get("topic", ""))
    intent_keywords = query_plan.get("intent_keywords", [])
    if not isinstance(intent_keywords, list):
        intent_keywords = []

    tier_counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    domain_counts: dict[str, int] = {}

    topic_tokens = _tokenize(topic)
    for keyword in intent_keywords:
        topic_tokens.update(_tokenize(str(keyword)))

    covered_sources = 0
    non_tier_a_domain_over_limit = False

    for source in sources:
        if not isinstance(source, dict):
            continue

        tier = str(source.get("authority_tier", "D")).upper()
        if tier not in tier_counts:
            tier = "D"
        tier_counts[tier] += 1

        domain = str(source.get("domain", "")).strip().lower()
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            if tier != "A" and domain_counts[domain] > 2:
                non_tier_a_domain_over_limit = True

        snippets = source.get("snippets", [])
        snippet_text = ""
        if isinstance(snippets, list):
            snippet_parts = []
            for snippet in snippets:
                if isinstance(snippet, dict):
                    snippet_parts.append(str(snippet.get("text", "")))
            snippet_text = " ".join(snippet_parts)
        content_tokens = _tokenize(f"{source.get('title', '')} {snippet_text}")
        if topic_tokens & content_tokens:
            covered_sources += 1

    source_count = len([source for source in sources if isinstance(source, dict)])
    keyword_coverage_ratio = covered_sources / source_count if source_count else 0.0

    checks = [
        {"prompt": "At least 3 sources are present", "answer": "Yes" if source_count >= 3 else "No"},
        {
            "prompt": "Authority threshold met (>=1 Tier A or >=2 Tier B)",
            "answer": "Yes" if (tier_counts["A"] >= 1 or tier_counts["B"] >= 2) else "No",
        },
        {
            "prompt": "Keyword coverage ratio is at least 0.5",
            "answer": "Yes" if keyword_coverage_ratio >= 0.5 else "No",
        },
        {
            "prompt": "No non-Tier-A domain has more than 2 sources",
            "answer": "Yes" if not non_tier_a_domain_over_limit else "No",
        },
    ]

    status = "pass" if all(check["answer"] == "Yes" for check in checks) else "fail"
    payload = {
        "status": status,
        "checks": checks,
        "metrics": {
            "tier_counts": tier_counts,
            "domain_counts": domain_counts,
            "keyword_coverage_ratio": round(keyword_coverage_ratio, 3),
        },
    }
    validate_json(payload, SCHEMA_PATH)
    return payload
