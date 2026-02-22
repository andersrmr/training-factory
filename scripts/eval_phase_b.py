from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import run_pipeline
from training_factory.settings import get_settings

PHASE = "phase_b"

CASES: dict[str, dict[str, str]] = {
    "C1": {"topic": "Power BI fundamentals", "audience": "novice"},
    "C2": {"topic": "Power Apps basics", "audience": "intermediate"},
    "C3": {
        "topic": "Enterprise ChatGPT governance and risk controls",
        "audience": "intermediate",
    },
    "C4": {
        "topic": "Power Platform ALM governance best practices",
        "audience": "intermediate",
    },
}

MODES: dict[str, dict[str, Any]] = {
    "M1": {"offline": True, "web": False, "search_provider": "offline"},
    "M2": {"offline": False, "web": True, "search_provider": "fallback"},
    "M3": {"offline": False, "web": True, "search_provider": "serpapi"},
}

CSV_COLUMNS = [
    "phase",
    "case_id",
    "mode_id",
    "topic",
    "audience",
    "web",
    "search_provider",
    "research_revision_count",
    "research_qa_status",
    "keyword_coverage_ratio",
    "tier_A_count",
    "tier_B_count",
    "tier_C_count",
    "tier_D_count",
    "unique_domains",
    "top_domain",
    "curriculum_modules_count",
    "brief_guidelines_count",
    "qa_status",
    "qa_authority_check",
    "qa_citation_validity_check",
    "notes",
]

_AUTHORITY_PROMPT = "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?"
_CITATION_PROMPT = "Does curriculum include references_used and are they valid research source IDs?"


@contextmanager
def _offline_override(enabled: bool):
    if not enabled:
        yield
        return

    previous = os.environ.get("TRAINING_FACTORY_OFFLINE")
    os.environ["TRAINING_FACTORY_OFFLINE"] = "1"
    get_settings.cache_clear()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TRAINING_FACTORY_OFFLINE", None)
        else:
            os.environ["TRAINING_FACTORY_OFFLINE"] = previous
        get_settings.cache_clear()


def _extract_bundle(state: Any) -> dict[str, Any]:
    state_data = state.model_dump() if hasattr(state, "model_dump") else dict(state)
    packaging = state_data.get("packaging", {})
    bundle = packaging.get("bundle") if isinstance(packaging, dict) else None
    if isinstance(bundle, dict):
        return bundle
    if isinstance(packaging, dict):
        return packaging
    return {}


def count_tiers(sources: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for source in sources:
        tier = str(source.get("authority_tier", "")).upper()
        if tier in counts:
            counts[tier] += 1
    return counts


def domain_stats(sources: list[dict[str, Any]]) -> tuple[int, str]:
    domains = [str(source.get("domain", "")).strip() for source in sources if source.get("domain")]
    if not domains:
        return 0, ""
    counts = Counter(domains)
    top_domain = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return len(counts), top_domain


def find_check_answer(qa_checks: list[dict[str, Any]], prompt_text: str) -> str:
    for check in qa_checks:
        if str(check.get("prompt", "")).strip() == prompt_text:
            answer = str(check.get("answer", "")).strip()
            if answer in {"Yes", "No"}:
                return answer
            return ""
    return ""


def _parse_ids(value: str, valid: list[str], label: str) -> list[str]:
    wanted = [item.strip() for item in value.split(",") if item.strip()]
    if not wanted:
        return list(valid)
    unknown = [item for item in wanted if item not in valid]
    if unknown:
        raise ValueError(f"Unknown {label}: {', '.join(unknown)}")
    return [item for item in valid if item in wanted]


def run_eval(
    *,
    out_root: str | Path = "out/eval/phase_b",
    case_ids: list[str] | None = None,
    mode_ids: list[str] | None = None,
) -> Path:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

    out_root_path = Path(out_root)
    out_root_path.mkdir(parents=True, exist_ok=True)

    selected_cases = case_ids or list(CASES.keys())
    selected_modes = mode_ids or list(MODES.keys())

    rows: list[dict[str, Any]] = []

    for case_id in selected_cases:
        case = CASES[case_id]
        for mode_id in selected_modes:
            mode = MODES[mode_id]
            topic = case["topic"]
            audience = case["audience"]
            web = bool(mode["web"])
            mode_search_provider = str(mode["search_provider"])
            pipeline_search_provider = (
                mode_search_provider if mode_search_provider in {"fallback", "serpapi"} else "fallback"
            )

            request_research = {
                "web": web,
                "search_provider": pipeline_search_provider,
            }

            with _offline_override(bool(mode["offline"])):
                state = run_pipeline(topic=topic, audience=audience, research=request_research)

            bundle = _extract_bundle(state)
            bundle_path = out_root_path / case_id / mode_id / "bundle.json"
            bundle_path.parent.mkdir(parents=True, exist_ok=True)
            bundle_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")

            research_qa = bundle.get("research_qa", {}) if isinstance(bundle, dict) else {}
            metrics = research_qa.get("metrics", {}) if isinstance(research_qa, dict) else {}
            research = bundle.get("research", {}) if isinstance(bundle, dict) else {}
            sources = research.get("sources", []) if isinstance(research, dict) else []
            sources = sources if isinstance(sources, list) else []

            tiers = count_tiers(sources)
            unique_domains, top_domain = domain_stats(sources)

            brief = bundle.get("brief", {}) if isinstance(bundle, dict) else {}
            key_guidelines = brief.get("key_guidelines", []) if isinstance(brief, dict) else []
            curriculum = bundle.get("curriculum", {}) if isinstance(bundle, dict) else {}
            modules = curriculum.get("modules", []) if isinstance(curriculum, dict) else []
            qa = bundle.get("qa", {}) if isinstance(bundle, dict) else {}
            qa_checks = qa.get("checks", []) if isinstance(qa, dict) else []
            qa_checks = qa_checks if isinstance(qa_checks, list) else []

            row = {
                "phase": PHASE,
                "case_id": case_id,
                "mode_id": mode_id,
                "topic": topic,
                "audience": audience,
                "web": web,
                "search_provider": mode_search_provider,
                "research_revision_count": int(getattr(state, "research_revision_count", 0)),
                "research_qa_status": str(research_qa.get("status", "")),
                "keyword_coverage_ratio": metrics.get("keyword_coverage_ratio", ""),
                "tier_A_count": tiers["A"],
                "tier_B_count": tiers["B"],
                "tier_C_count": tiers["C"],
                "tier_D_count": tiers["D"],
                "unique_domains": unique_domains,
                "top_domain": top_domain,
                "curriculum_modules_count": len(modules) if isinstance(modules, list) else 0,
                "brief_guidelines_count": len(key_guidelines) if isinstance(key_guidelines, list) else 0,
                "qa_status": str(qa.get("status", "")),
                "qa_authority_check": find_check_answer(qa_checks, _AUTHORITY_PROMPT),
                "qa_citation_validity_check": find_check_answer(qa_checks, _CITATION_PROMPT),
                "notes": "",
            }
            rows.append(row)

    summary_path = out_root_path / "summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase B eval matrix and write CSV summary.")
    parser.add_argument("--out-root", default="out/eval/phase_b", help="Output root directory.")
    parser.add_argument(
        "--cases",
        default="C1,C2,C3,C4",
        help="Comma-separated case IDs (default: C1,C2,C3,C4).",
    )
    parser.add_argument(
        "--modes",
        default="M1,M2,M3",
        help="Comma-separated mode IDs (default: M1,M2,M3).",
    )
    args = parser.parse_args()

    try:
        case_ids = _parse_ids(args.cases, list(CASES.keys()), "case IDs")
        mode_ids = _parse_ids(args.modes, list(MODES.keys()), "mode IDs")
    except ValueError as exc:
        raise SystemExit(str(exc))

    summary = run_eval(out_root=args.out_root, case_ids=case_ids, mode_ids=mode_ids)
    print(f"Wrote summary to {summary}")


if __name__ == "__main__":
    main()
