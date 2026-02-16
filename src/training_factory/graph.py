from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from training_factory.agents.brief import generate_brief
from training_factory.agents.curriculum import generate_curriculum
from training_factory.agents.qa import generate_qa
from training_factory.agents.slides import generate_slides
from training_factory.state import TrainingState
from training_factory.utils.json_schema import validate_json

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT_DIR / "schemas"


class GraphState(TypedDict, total=False):
    request: dict[str, Any]
    brief: dict[str, Any]
    curriculum: dict[str, Any]
    slides: dict[str, Any]
    qa: dict[str, Any]
    packaging: dict[str, Any]
    revision_count: int


def _brief_node(state: GraphState) -> dict[str, Any]:
    brief = generate_brief(state["request"])
    return {"brief": brief}


def _curriculum_node(state: GraphState) -> dict[str, Any]:
    curriculum = generate_curriculum(state["brief"])
    return {"curriculum": curriculum}


def _slides_node(state: GraphState) -> dict[str, Any]:
    slides = generate_slides(state["curriculum"])
    revision_count = int(state.get("revision_count", 0))
    if state.get("qa", {}).get("status") == "fail":
        revision_count += 1
    return {"slides": slides, "revision_count": revision_count}


def _qa_node(state: GraphState) -> dict[str, Any]:
    qa = generate_qa(state["slides"])
    return {"qa": qa}


def _route_after_qa(state: GraphState) -> str:
    qa_status = state.get("qa", {}).get("status")
    revision_count = int(state.get("revision_count", 0))
    if qa_status == "fail" and revision_count < 1:
        return "slides"
    return "package"


def _package_node(state: GraphState) -> dict[str, Any]:
    packaging = {
        "request": state["request"],
        "brief": state["brief"],
        "curriculum": state["curriculum"],
        "slides": state["slides"],
        "qa": state["qa"],
    }
    validate_json(packaging, SCHEMA_DIR / "bundle.schema.json")
    return {
        "packaging": packaging,
        "revision_count": int(state.get("revision_count", 0)),
    }


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("brief", _brief_node)
    graph.add_node("curriculum", _curriculum_node)
    graph.add_node("slides", _slides_node)
    graph.add_node("qa", _qa_node)
    graph.add_node("package", _package_node)

    graph.add_edge(START, "brief")
    graph.add_edge("brief", "curriculum")
    graph.add_edge("curriculum", "slides")
    graph.add_edge("slides", "qa")
    graph.add_conditional_edges(
        "qa",
        _route_after_qa,
        {"slides": "slides", "package": "package"},
    )
    graph.add_edge("package", END)

    return graph.compile()


def run_pipeline(topic: str, audience: str) -> TrainingState:
    app = build_graph()
    initial = TrainingState(request={"topic": topic, "audience": audience})
    result = app.invoke(initial.model_dump())
    return TrainingState.model_validate(result)
