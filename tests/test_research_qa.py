from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.research import generate_research
from training_factory.agents.research_qa import generate_research_qa


def test_research_qa_passes_for_fallback_power_bi() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = generate_research(request)

    payload = generate_research_qa(research, request)

    assert payload["status"] == "pass"
    assert all(check["answer"] == "Yes" for check in payload["checks"])


def test_research_qa_fails_for_low_quality_sources() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = {
        "query_plan": {"queries": ["x"], "intent_keywords": ["governance"], "preferred_domains": []},
        "sources": [
            {
                "id": "src_001",
                "title": "misc notes",
                "url": "https://example.com/a",
                "domain": "example.com",
                "publisher": "example.com",
                "doc_type": "",
                "authority_tier": "D",
                "score": 0.1,
                "snippets": [{"heading": "search_snippet", "text": "random text", "loc": "search"}],
            },
            {
                "id": "src_002",
                "title": "another note",
                "url": "https://example.com/b",
                "domain": "example.com",
                "publisher": "example.com",
                "doc_type": "",
                "authority_tier": "D",
                "score": 0.2,
                "snippets": [{"heading": "search_snippet", "text": "unrelated content", "loc": "search"}],
            },
        ],
        "context_pack": "x",
    }

    payload = generate_research_qa(research, request)

    assert payload["status"] == "fail"
    assert any(check["answer"] == "No" for check in payload["checks"])
