from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import training_factory.agents.research as research_module
from training_factory.agents.research import generate_research
from training_factory.research.providers import SearchResult


class _StaticProvider:
    def search(self, query: str, *, num_results: int = 10) -> list[SearchResult]:
        _ = (query, num_results)
        return [
            SearchResult(
                title="Power Platform ALM",
                url="https://learn.microsoft.com/power-platform/alm/overview-alm",
                snippet="governance lifecycle",
                source="learn.microsoft.com",
                rank=1,
            ),
            SearchResult(
                title="Power BI guidance",
                url="https://learn.microsoft.com/power-bi/guidance/",
                snippet="best practices governance",
                source="learn.microsoft.com",
                rank=2,
            ),
        ]


def test_query_plan_includes_power_bi_anchor_queries() -> None:
    payload = generate_research(
        {
            "topic": "Power BI fundamentals",
            "audience": "novice",
            "research": {"web": False, "search_provider": "fallback"},
        }
    )

    query_plan = payload["query_plan"]
    queries = query_plan["queries"]

    assert query_plan["product"] == "power_bi"
    assert any("site:learn.microsoft.com/power-bi" in query for query in queries)
    assert any("site:learn.microsoft.com/fabric" in query for query in queries)
    assert any("site:learn.microsoft.com/power-bi" in query for query in queries[:3])


def test_power_bi_url_boost_ranks_above_power_platform(monkeypatch) -> None:
    monkeypatch.setattr(research_module, "get_search_provider", lambda name, web=False: _StaticProvider())

    payload = generate_research(
        {
            "topic": "Power BI fundamentals",
            "audience": "novice",
            "research": {"web": False, "search_provider": "fallback"},
        }
    )

    urls = [source["url"] for source in payload["sources"]]

    assert "https://learn.microsoft.com/power-bi/guidance/" in urls
    assert "https://learn.microsoft.com/power-platform/alm/overview-alm" in urls
    assert urls.index("https://learn.microsoft.com/power-bi/guidance/") < urls.index(
        "https://learn.microsoft.com/power-platform/alm/overview-alm"
    )
