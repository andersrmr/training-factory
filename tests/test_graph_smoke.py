from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import build_graph
from training_factory.state import TrainingState
from training_factory.utils.json_schema import validate_json


def test_graph_smoke() -> None:
    graph = build_graph()
    initial = TrainingState(request={"topic": "Intro to Python", "audience": "novice"}).model_dump()
    result = graph.invoke(initial)
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "bundle.schema.json"
    validate_json(result["packaging"], schema_path)

    assert result["packaging"]["brief"]["topic"] == "Intro to Python"
    assert result["packaging"]["lab"]["labs"]
    assert result["packaging"]["slides"]["deck"]
    assert "readme_md" in result["packaging"]["templates"]
    assert "runbook_md" in result["packaging"]["templates"]
    assert result["packaging"]["templates"]["readme_md"]["content"].strip()
    assert result["packaging"]["templates"]["runbook_md"]["content"].strip()
