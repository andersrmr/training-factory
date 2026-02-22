from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.brief import generate_brief
from training_factory.agents.curriculum import generate_curriculum
from training_factory.agents.research import generate_research
from training_factory.utils.json_schema import validate_json


def test_curriculum_citations_are_grounded_to_research_sources() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = generate_research(request)
    brief = generate_brief(request, research)
    curriculum = generate_curriculum(brief, research)

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "curriculum.schema.json"
    validate_json(curriculum, schema_path)

    research_ids = {
        str(source.get("id"))
        for source in research.get("sources", [])
        if isinstance(source, dict) and str(source.get("id", "")).strip()
    }

    references_used = curriculum.get("references_used", [])
    assert isinstance(references_used, list)
    assert len(references_used) >= 1
    assert all(source_id in research_ids for source_id in references_used)

    modules = curriculum.get("modules", [])
    assert isinstance(modules, list)
    assert len(modules) >= 1
    for module in modules:
        assert isinstance(module, dict)
        sources = module.get("sources", [])
        assert isinstance(sources, list)
        assert len(sources) >= 1
        assert all(source_id in research_ids for source_id in sources)
