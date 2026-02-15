from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import run_pipeline
from training_factory.utils.json_schema import validate_json


def test_graph_smoke() -> None:
    state = run_pipeline(topic="Intro to Python", audience="novice")
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "bundle.schema.json"
    validate_json(state.packaging, schema_path)

    assert state.request["topic"] == "Intro to Python"
    assert state.brief
    assert state.curriculum
    assert state.slides
    assert state.qa
    assert state.packaging
    assert state.revision_count == 1
