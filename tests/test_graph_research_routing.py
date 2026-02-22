from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import build_graph
from training_factory.state import TrainingState


def _brief(request: dict, research: dict) -> dict:
    source_id = "src_001"
    sources = research.get("sources", [])
    if isinstance(sources, list) and sources and isinstance(sources[0], dict):
        source_id = str(sources[0].get("id", source_id))
    return {
        "topic": request.get("topic", "T"),
        "audience": request.get("audience", "A"),
        "goals": ["g1"],
        "constraints": ["c1"],
        "references_used": [source_id],
        "key_guidelines": [
            {
                "guideline": "Use grounded sources.",
                "rationale": "Improves reliability.",
                "sources": [source_id],
            }
        ],
    }


def _curriculum(_: dict) -> dict:
    return {"modules": [{"title": "M1", "duration_minutes": 10}]}


def _slides(_: dict) -> dict:
    return {"deck": [{"slide": 1, "title": "S1", "bullets": ["b1"]}]}


def _lab(_: dict) -> dict:
    return {"labs": [{"title": "L1", "instructions": ["i1"], "expected_outcome": "o1"}]}


def _templates(_: dict) -> dict:
    return {"readme_md": {"content": "r"}, "runbook_md": {"content": "r"}}


def test_research_qa_fail_retries_once_then_proceeds(monkeypatch) -> None:
    import training_factory.graph as graph_module

    calls = {"research": 0}

    low_quality_research = {
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

    good_research = {
        "query_plan": {
            "queries": ["Power BI basics governance"],
            "intent_keywords": ["power", "governance"],
            "preferred_domains": ["learn.microsoft.com"],
        },
        "sources": [
            {
                "id": "src_001",
                "title": "Power BI governance guidance",
                "url": "https://learn.microsoft.com/power-bi/guidance/",
                "domain": "learn.microsoft.com",
                "publisher": "learn.microsoft.com",
                "doc_type": "guide",
                "authority_tier": "A",
                "score": 5.0,
                "snippets": [
                    {
                        "heading": "search_snippet",
                        "text": "Power BI governance and security best practices.",
                        "loc": "search",
                    }
                ],
            },
            {
                "id": "src_002",
                "title": "Power BI lifecycle and ALM",
                "url": "https://learn.microsoft.com/power-bi/enterprise/powerbi-implementation-planning-alm",
                "domain": "learn.microsoft.com",
                "publisher": "learn.microsoft.com",
                "doc_type": "guide",
                "authority_tier": "A",
                "score": 4.8,
                "snippets": [
                    {
                        "heading": "search_snippet",
                        "text": "Lifecycle and ALM for Power BI deployments.",
                        "loc": "search",
                    }
                ],
            },
            {
                "id": "src_003",
                "title": "NIST risk management",
                "url": "https://www.nist.gov/cyberframework",
                "domain": "nist.gov",
                "publisher": "nist.gov",
                "doc_type": "",
                "authority_tier": "A",
                "score": 4.6,
                "snippets": [
                    {
                        "heading": "search_snippet",
                        "text": "Risk management guidance applicable to governance.",
                        "loc": "search",
                    }
                ],
            },
        ],
        "context_pack": "topic + sources",
    }

    def research_fn(_: dict) -> dict:
        calls["research"] += 1
        if calls["research"] == 1:
            return low_quality_research
        return good_research

    monkeypatch.setattr(graph_module, "generate_research", research_fn)
    monkeypatch.setattr(graph_module, "generate_brief", _brief)
    monkeypatch.setattr(graph_module, "generate_curriculum", _curriculum)
    monkeypatch.setattr(graph_module, "generate_slides", _slides)
    monkeypatch.setattr(graph_module, "generate_lab", _lab)
    monkeypatch.setattr(graph_module, "generate_templates", _templates)
    monkeypatch.setattr(graph_module, "generate_qa", lambda *_args: {"status": "pass", "checks": []})

    graph = build_graph()
    result = graph.invoke(TrainingState(request={"topic": "X", "audience": "Y"}).model_dump())

    assert calls["research"] == 2
    assert result["research_revision_count"] == 1
    assert result["packaging"]["research_qa"]["status"] == "pass"
