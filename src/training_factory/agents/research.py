from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import urlparse

from training_factory.research import fetch_extract
from training_factory.research.providers import SearchResult
from training_factory.research.registry import get_search_provider

_MAX_CONTEXT_PACK_CHARS = 6000
_MAX_RESULTS_PER_QUERY = 10
_MAX_SELECTED_SOURCES = 8
_MAX_ENRICHED_SOURCES = 4
_DOMAIN_CAP = 2

_TIER_A_DOMAINS = {
    "learn.microsoft.com",
    "docs.microsoft.com",
    "nist.gov",
    "owasp.org",
}
_TIER_B_DOMAINS = {
    "aws.amazon.com",
    "cloud.google.com",
    "azure.microsoft.com",
    "mckinsey.com",
    "deloitte.com",
    "accenture.com",
    "pwc.com",
}
_TIER_C_DOMAINS = {
    "medium.com",
    "linkedin.com",
    "dev.to",
    "substack.com",
}
_TIER_SCORES = {"A": 4.0, "B": 2.5, "C": 1.2, "D": 0.3}
_INTENT_KEYWORDS = [
    "best practices",
    "governance",
    "lifecycle",
    "security",
    "alm",
    "risk",
    "operating model",
]


def _is_power_platform_topic(topic: str) -> bool:
    topic_lower = topic.lower()
    return any(
        token in topic_lower
        for token in ("power bi", "power apps", "power platform", "dataverse", "alm")
    )


def _detect_product(topic: str) -> str:
    topic_lower = topic.lower()
    if "power bi" in topic_lower:
        return "power_bi"
    if "power apps" in topic_lower:
        return "power_apps"
    if (
        "power platform" in topic_lower
        or "dataverse" in topic_lower
        or "power automate" in topic_lower
    ):
        return "power_platform"
    if "enterprise chatgpt" in topic_lower or "chatgpt" in topic_lower:
        return "enterprise_chatgpt"
    return "generic"


def _build_query_plan(topic: str) -> dict[str, Any]:
    product = _detect_product(topic)
    base_queries = [
        f"{topic} best practices",
        f"{topic} governance operating model",
        f"{topic} lifecycle ALM",
        f"{topic} security risk controls",
    ]
    anchor_queries: list[str] = []
    if product == "power_bi":
        anchor_queries = [
            "site:learn.microsoft.com/power-bi power bi guidance best practices",
            "site:learn.microsoft.com/fabric powerbi admin security governance",
        ]
    elif product in {"power_apps", "power_platform"}:
        anchor_queries = [
            "site:learn.microsoft.com/power-platform alm governance best practices",
            "site:learn.microsoft.com/power-apps governance environment strategy",
        ]
    elif product == "enterprise_chatgpt":
        anchor_queries = [
            "enterprise chatgpt governance risk controls best practices",
            "site:nist.gov generative ai risk management",
        ]
    queries = anchor_queries + base_queries
    preferred_domains = ["learn.microsoft.com"] if _is_power_platform_topic(topic) else []
    return {
        "queries": queries,
        "intent_keywords": list(_INTENT_KEYWORDS),
        "preferred_domains": preferred_domains,
        "product": product,
    }


def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    return host


def _matches_domain(domain: str, candidates: set[str]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)


def _authority_tier(domain: str) -> str:
    if _matches_domain(domain, _TIER_A_DOMAINS):
        return "A"
    if _matches_domain(domain, _TIER_B_DOMAINS):
        return "B"
    if _matches_domain(domain, _TIER_C_DOMAINS):
        return "C"
    return "D"


def _tokenize(value: str) -> set[str]:
    normalized = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return {token for token in normalized.split() if len(token) > 2}


def _keyword_overlap_score(topic: str, intent_keywords: list[str], title: str, snippet: str) -> float:
    topic_tokens = _tokenize(topic)
    for keyword in intent_keywords:
        topic_tokens.update(_tokenize(keyword))
    content_tokens = _tokenize(f"{title} {snippet}")
    overlap_count = len(topic_tokens & content_tokens)
    return float(overlap_count) * 0.35


def _best_effort_doc_type(url: str) -> str:
    path = urlparse(url).path.lower()
    if "/blog/" in path:
        return "blog"
    if "/docs/" in path or "/documentation" in path:
        return "documentation"
    if "/learn/" in path or "/training/" in path:
        return "guide"
    return ""


def _best_effort_publisher(domain: str, source: str) -> str:
    if source:
        return source
    if not domain:
        return ""
    return domain


def _score_result(
    *,
    topic: str,
    intent_keywords: list[str],
    preferred_domains: list[str],
    product: str,
    result: SearchResult,
    domain: str,
) -> tuple[str, float]:
    tier = _authority_tier(domain)
    score = _TIER_SCORES[tier]
    score += _keyword_overlap_score(topic, intent_keywords, result.title, result.snippet)
    if any(domain == d or domain.endswith(f".{d}") for d in preferred_domains):
        score += 1.0
    url_lower = result.url.lower()
    topic_lower = topic.lower()
    topic_has_alm_or_lifecycle = "alm" in topic_lower or "lifecycle" in topic_lower
    if product == "power_bi":
        if "/power-bi/" in url_lower or "/fabric/" in url_lower:
            score += 0.6
        if ("/power-platform/" in url_lower or "/power-apps/" in url_lower) and not topic_has_alm_or_lifecycle:
            score -= 0.4
    elif product == "power_apps":
        if "/power-apps/" in url_lower:
            score += 0.6
        if "/power-bi/" in url_lower:
            score -= 0.2
    elif product == "power_platform":
        if "/power-platform/" in url_lower:
            score += 0.6
        if "/power-bi/" in url_lower:
            score -= 0.2
    elif product == "enterprise_chatgpt":
        if domain in {"nist.gov", "owasp.org", "learn.microsoft.com", "cloud.google.com", "aws.amazon.com"}:
            score += 0.6
    return tier, round(score, 3)


def _build_context_pack(topic: str, audience: str, sources: list[dict[str, Any]]) -> str:
    lines = [
        f"Topic: {topic}",
        f"Audience: {audience}",
        "",
        "Sources:",
    ]
    for source in sources:
        lines.append(
            f"- {source['id']} | {source['authority_tier']} | {source['title']} | {source['url']}"
        )
        snippet_items = source.get("snippets", [])
        for snippet in snippet_items[:2]:
            text = snippet.get("text", "").strip()
            if text:
                lines.append(f"  - {text}")
    text = "\n".join(lines)
    if len(text) <= _MAX_CONTEXT_PACK_CHARS:
        return text
    return text[: _MAX_CONTEXT_PACK_CHARS - 16].rstrip() + "\n[TRUNCATED]"


def generate_research(request: dict[str, Any]) -> dict[str, Any]:
    topic = str(request.get("topic", "")).strip()
    audience = str(request.get("audience", "")).strip()
    research_cfg = request.get("research", {}) if isinstance(request.get("research"), dict) else {}
    web = bool(research_cfg.get("web", False))
    search_provider = str(research_cfg.get("search_provider", "fallback"))
    provider = get_search_provider(name=search_provider, web=web)

    query_plan = _build_query_plan(topic)
    seen_urls: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for query in query_plan["queries"]:
        for item in provider.search(query, num_results=_MAX_RESULTS_PER_QUERY):
            if not item.url or item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            domain = _extract_domain(item.url)
            authority_tier, score = _score_result(
                topic=topic,
                intent_keywords=query_plan["intent_keywords"],
                preferred_domains=query_plan["preferred_domains"],
                product=str(query_plan["product"]),
                result=item,
                domain=domain,
            )
            candidates.append(
                {
                    "title": item.title,
                    "url": item.url,
                    "domain": domain,
                    "publisher": _best_effort_publisher(domain, item.source),
                    "doc_type": _best_effort_doc_type(item.url),
                    "authority_tier": authority_tier,
                    "score": score,
                    "snippets": [
                        {
                            "heading": "search_snippet",
                            "text": item.snippet or "",
                            "loc": "search",
                        }
                    ],
                }
            )

    candidates.sort(key=lambda row: (-float(row["score"]), row["url"]))

    selected: list[dict[str, Any]] = []
    per_domain_counts: dict[str, int] = {}
    for item in candidates:
        domain = str(item["domain"])
        tier = str(item["authority_tier"])
        count = per_domain_counts.get(domain, 0)
        if tier != "A" and count >= _DOMAIN_CAP:
            continue
        per_domain_counts[domain] = count + 1
        selected.append(item)
        if len(selected) >= _MAX_SELECTED_SOURCES:
            break

    for idx, item in enumerate(selected, start=1):
        item["id"] = f"src_{idx:03d}"

    if web and selected:
        enrichment_keywords = list(query_plan["intent_keywords"])
        enrichment_keywords.extend(sorted(_tokenize(topic)))
        tier_priority = {"A": 0, "B": 1, "C": 2, "D": 3}
        candidate_order = sorted(
            range(len(selected)),
            key=lambda idx: (
                tier_priority.get(str(selected[idx].get("authority_tier", "D")), 9),
                -float(selected[idx].get("score", 0.0)),
                str(selected[idx].get("url", "")),
            ),
        )
        for source_idx in candidate_order[:_MAX_ENRICHED_SOURCES]:
            source = selected[source_idx]
            html = fetch_extract.fetch_url(str(source.get("url", "")))
            enriched_snippets = fetch_extract.extract_snippets(
                html,
                intent_keywords=enrichment_keywords,
                max_snippets=4,
            )
            if enriched_snippets:
                source["snippets"] = (enriched_snippets + list(source.get("snippets", [])))[:4]
            source["retrieved_at"] = date.today().isoformat()

    context_pack = _build_context_pack(topic, audience, selected)
    return {
        "query_plan": query_plan,
        "sources": selected,
        "context_pack": context_pack,
    }
