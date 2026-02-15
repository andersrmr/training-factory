from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import run_pipeline


def test_graph_smoke() -> None:
    state = run_pipeline(topic="Intro to Python", audience="novice")

    assert state.request["topic"] == "Intro to Python"
    assert state.brief
    assert state.curriculum
    assert state.slides
    assert state.qa
    assert state.packaging
    assert state.revision_count == 1
