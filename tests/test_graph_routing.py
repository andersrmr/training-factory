from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.graph import build_graph
from training_factory.state import TrainingState


def _brief(_: dict, __: dict) -> dict:
    return {
        "topic": "T",
        "audience": "A",
        "goals": ["g1"],
        "constraints": ["c1"],
        "references_used": ["src_001"],
        "key_guidelines": [
            {
                "guideline": "Use authoritative sources.",
                "rationale": "Improves correctness.",
                "sources": ["src_001"],
            }
        ],
    }


def _curriculum(_: dict) -> dict:
    return {"modules": [{"title": "M1", "duration_minutes": 10}]}


def _slides(_: dict) -> dict:
    return {"deck": [{"slide": 1, "title": "S1", "bullets": ["b1"]}]}


def test_qa_pass_routes_to_package(monkeypatch) -> None:
    import training_factory.graph as graph_module

    calls = {"slides": 0}

    def slides_fn(curriculum: dict) -> dict:
        calls["slides"] += 1
        return _slides(curriculum)

    monkeypatch.setattr(graph_module, "generate_brief", _brief)
    monkeypatch.setattr(graph_module, "generate_curriculum", _curriculum)
    monkeypatch.setattr(graph_module, "generate_slides", slides_fn)
    monkeypatch.setattr(
        graph_module,
        "generate_qa",
        lambda _slides, _lab, _templates: {"status": "pass", "checks": []},
    )

    graph = build_graph()
    result = graph.invoke(TrainingState(request={"topic": "X", "audience": "Y"}).model_dump())

    assert calls["slides"] == 1
    assert result["packaging"]["qa"]["status"] == "pass"
    assert result["revision_count"] == 0


def test_qa_fail_retries_once_then_packages(monkeypatch) -> None:
    import training_factory.graph as graph_module

    calls = {"slides": 0, "qa": 0}

    def slides_fn(curriculum: dict) -> dict:
        calls["slides"] += 1
        return _slides(curriculum)

    def qa_fn(_slides: dict, _lab: dict, _templates: dict) -> dict:
        calls["qa"] += 1
        if calls["qa"] == 1:
            return {"status": "fail", "checks": []}
        return {"status": "pass", "checks": []}

    monkeypatch.setattr(graph_module, "generate_brief", _brief)
    monkeypatch.setattr(graph_module, "generate_curriculum", _curriculum)
    monkeypatch.setattr(graph_module, "generate_slides", slides_fn)
    monkeypatch.setattr(graph_module, "generate_qa", qa_fn)

    graph = build_graph()
    result = graph.invoke(TrainingState(request={"topic": "X", "audience": "Y"}).model_dump())

    assert calls["slides"] == 2
    assert result["packaging"]["qa"]["status"] == "pass"
    assert result["revision_count"] == 1


def test_qa_fail_with_revision_limit_packages_without_retry(monkeypatch) -> None:
    import training_factory.graph as graph_module

    calls = {"slides": 0}

    def slides_fn(curriculum: dict) -> dict:
        calls["slides"] += 1
        return _slides(curriculum)

    monkeypatch.setattr(graph_module, "generate_brief", _brief)
    monkeypatch.setattr(graph_module, "generate_curriculum", _curriculum)
    monkeypatch.setattr(graph_module, "generate_slides", slides_fn)
    monkeypatch.setattr(
        graph_module,
        "generate_qa",
        lambda _slides, _lab, _templates: {"status": "fail", "checks": []},
    )

    graph = build_graph()
    result = graph.invoke(
        TrainingState(request={"topic": "X", "audience": "Y"}, revision_count=1).model_dump()
    )

    assert calls["slides"] == 1
    assert result["packaging"]["qa"]["status"] == "fail"
    assert result["revision_count"] == 1
