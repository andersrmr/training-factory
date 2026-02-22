from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.research import generate_research
from training_factory.utils.json_schema import validate_json


def test_generate_research_offline_shape_and_scoring() -> None:
    payload = generate_research({"topic": "Power BI basics", "audience": "novice"})

    assert isinstance(payload, dict)
    assert "query_plan" in payload
    assert "sources" in payload
    assert "context_pack" in payload

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "research.schema.json"
    validate_json(payload, schema_path)

    sources = payload["sources"]
    assert sources
    assert any("learn.microsoft.com" in source["url"] for source in sources)

    scores = [float(source["score"]) for source in sources]
    assert scores == sorted(scores, reverse=True)

    context_pack = payload["context_pack"]
    assert "src_" in context_pack
    assert "http" in context_pack
