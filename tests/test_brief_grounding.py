from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.brief import generate_brief
from training_factory.agents.research import generate_research


def test_brief_uses_research_source_ids_offline() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = generate_research(request)
    brief = generate_brief(request, research)

    research_ids = {source["id"] for source in research["sources"]}

    references_used = brief.get("references_used", [])
    assert isinstance(references_used, list)
    assert len(references_used) >= 1
    assert all(source_id in research_ids for source_id in references_used)

    key_guidelines = brief.get("key_guidelines", [])
    assert isinstance(key_guidelines, list)
    assert len(key_guidelines) >= 1
    for guideline in key_guidelines:
        sources = guideline.get("sources", [])
        assert isinstance(sources, list)
        assert len(sources) >= 1
        assert all(source_id in research_ids for source_id in sources)
