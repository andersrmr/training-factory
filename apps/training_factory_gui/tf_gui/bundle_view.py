from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def safe_read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def load_bundle_from_path(path: str) -> dict[str, Any]:
    trimmed = path.strip()
    if not trimmed:
        raise ValueError("Bundle path is empty.")

    bundle_path = Path(trimmed)
    if not bundle_path.exists():
        raise ValueError(f"Bundle path does not exist: {bundle_path}")
    if not bundle_path.is_file():
        raise ValueError(f"Bundle path is not a file: {bundle_path}")

    try:
        payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError(f"Bundle file is not valid UTF-8: {bundle_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in bundle file: {bundle_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Bundle JSON must be an object at top level.")
    return payload


def load_bundle_from_upload(uploaded_file: Any) -> dict[str, Any]:
    if uploaded_file is None:
        raise ValueError("No uploaded file provided.")

    try:
        payload = json.load(uploaded_file)
    except json.JSONDecodeError as exc:
        raise ValueError("Uploaded file is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Uploaded bundle JSON must be an object at top level.")
    return payload


def _derive_mode(bundle: dict[str, Any]) -> str:
    request = _as_dict(bundle.get("request"))
    request_research = _as_dict(request.get("research"))
    web = bool(request_research.get("web", False))
    search_provider = str(request_research.get("search_provider", "")).strip().lower()

    if not web:
        return "M1"
    if search_provider == "serpapi":
        return "M3"
    if search_provider == "fallback":
        return "M2"
    return "(missing)"


def _compute_tier_counts_from_sources(sources: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for source in sources:
        tier = str(source.get("authority_tier", "")).upper()
        if tier in counts:
            counts[tier] += 1
    return counts


def extract_run_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    request = _as_dict(bundle.get("request"))
    request_research = _as_dict(request.get("research"))
    brief = _as_dict(bundle.get("brief"))
    research = _as_dict(bundle.get("research"))
    research_qa = _as_dict(bundle.get("research_qa"))
    metrics = _as_dict(research_qa.get("metrics"))
    query_plan = _as_dict(research.get("query_plan"))
    qa = _as_dict(bundle.get("qa"))

    sources = [source for source in _as_list(research.get("sources")) if isinstance(source, dict)]

    tier_counts = metrics.get("tier_counts")
    if not isinstance(tier_counts, dict):
        tier_counts = _compute_tier_counts_from_sources(sources)

    domain_counts = metrics.get("domain_counts")
    if isinstance(domain_counts, dict):
        domain_count = len(domain_counts)
    else:
        domains = {
            str(source.get("domain", "")).strip()
            for source in sources
            if str(source.get("domain", "")).strip()
        }
        domain_count = len(domains)

    curriculum = _as_dict(bundle.get("curriculum"))
    request_topic = request.get("topic")
    request_audience = request.get("audience")
    common_topic = request_topic or brief.get("topic") or curriculum.get("topic")
    common_audience = request_audience or brief.get("audience") or curriculum.get("audience")

    return {
        "topic": common_topic or "(missing)",
        "audience": common_audience or "(missing)",
        "mode": _derive_mode(bundle),
        "product": query_plan.get("product") or "(missing)",
        "qa_status": qa.get("status") or "(missing)",
        "tier_counts": tier_counts,
        "domain_count": domain_count,
        "search_provider": request_research.get("search_provider") or "(missing)",
        "web": bool(request_research.get("web", False)),
    }


def extract_sources_table(bundle: dict[str, Any]) -> Any:
    research = _as_dict(bundle.get("research"))
    sources = [source for source in _as_list(research.get("sources")) if isinstance(source, dict)]

    rows: list[dict[str, Any]] = []
    for source in sources:
        snippets = _as_list(source.get("snippets"))
        row = {
            "tier": source.get("authority_tier", ""),
            "domain": source.get("domain", ""),
            "title": source.get("title", ""),
            "url": source.get("url", ""),
            "score": source.get("score", ""),
            "snippet_count": len(snippets),
        }
        rows.append(row)

    try:
        import pandas as pd  # type: ignore

        return pd.DataFrame(rows)
    except Exception:
        return rows


def render_bundle_summary(st: Any, bundle: dict[str, Any]) -> None:
    brief = _as_dict(bundle.get("brief"))
    curriculum = _as_dict(bundle.get("curriculum"))
    qa = _as_dict(bundle.get("qa"))

    references_used = _as_list(brief.get("references_used"))
    key_guidelines = _as_list(brief.get("key_guidelines"))
    modules = _as_list(curriculum.get("modules"))
    qa_checks = [check for check in _as_list(qa.get("checks")) if isinstance(check, dict)]

    st.subheader("Parsed Summary")
    st.markdown(f"- `brief.references_used`: **{len(references_used)}**")
    st.markdown(f"- `brief.key_guidelines`: **{len(key_guidelines)}**")
    st.markdown(f"- `curriculum.modules`: **{len(modules)}**")
    st.markdown(f"- `qa.status`: **{qa.get('status', '(missing)')}**")

    st.subheader("QA Checks")
    if not qa_checks:
        st.write("(missing)")
        return

    for check in qa_checks:
        prompt = str(check.get("prompt", "(missing)"))
        answer = str(check.get("answer", "(missing)"))
        st.markdown(f"- **{answer}** — {prompt}")
