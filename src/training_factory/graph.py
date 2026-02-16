from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from training_factory.agents.brief import generate_brief
from training_factory.agents.curriculum import generate_curriculum
from training_factory.agents.lab import generate_lab
from training_factory.agents.qa import generate_qa
from training_factory.agents.slides import generate_slides
from training_factory.agents.templates import generate_templates
from training_factory.state import TrainingState
from training_factory.utils.json_schema import validate_json

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT_DIR / "schemas"


class GraphState(TypedDict):
    request: dict[str, Any]
    brief: dict[str, Any]
    curriculum: dict[str, Any]
    lab: dict[str, Any]
    slides: dict[str, Any]
    templates: dict[str, Any]
    qa: dict[str, Any]
    packaging: dict[str, Any]
    revision_count: int
    route: str


def _brief_node(state: GraphState) -> dict[str, Any]:
    brief = generate_brief(state["request"])
    return {"brief": brief}


def _curriculum_node(state: GraphState) -> dict[str, Any]:
    curriculum = generate_curriculum(state["brief"])
    return {"curriculum": curriculum}


def _slides_node(state: GraphState) -> dict[str, Any]:
    slides = generate_slides(state["curriculum"])
    return {"slides": slides}


def _lab_node(state: GraphState) -> dict[str, Any]:
    lab = generate_lab(state["curriculum"])
    return {"lab": lab}


def _qa_node(state: GraphState) -> dict[str, Any]:
    qa = generate_qa(state["templates"])
    return {"qa": qa}


def _templates_node(state: GraphState) -> dict[str, Any]:
    templates = generate_templates(state["slides"])
    return {"templates": templates}


def _retry_gate_node(state: GraphState) -> dict[str, Any]:
    qa_status = state.get("qa", {}).get("status")
    revision_count = int(state.get("revision_count", 0))
    if qa_status == "fail" and revision_count < 1:
        return {"revision_count": revision_count + 1, "route": "slides"}
    return {"route": "package"}


def _route_after_retry_gate(state: GraphState) -> str:
    return state.get("route", "package")


def _package_node(state: GraphState) -> dict[str, Any]:
    packaging = {
        "request": state["request"],
        "brief": state["brief"],
        "curriculum": state["curriculum"],
        "lab": state["lab"],
        "slides": state["slides"],
        "templates": state["templates"],
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
    graph.add_node("lab", _lab_node)
    graph.add_node("slides", _slides_node)
    graph.add_node("templates", _templates_node)
    graph.add_node("qa", _qa_node)
    graph.add_node("retry_gate", _retry_gate_node)
    graph.add_node("package", _package_node)

    graph.add_edge(START, "brief")
    graph.add_edge("brief", "curriculum")
    graph.add_edge("curriculum", "lab")
    graph.add_edge("lab", "slides")
    graph.add_edge("slides", "templates")
    graph.add_edge("templates", "qa")
    graph.add_edge("qa", "retry_gate")
    graph.add_conditional_edges(
        "retry_gate",
        _route_after_retry_gate,
        {"slides": "slides", "package": "package"},
    )
    graph.add_edge("package", END)

    return graph.compile()


def run_pipeline(topic: str, audience: str) -> TrainingState:
    app = build_graph()
    initial = TrainingState(request={"topic": topic, "audience": audience})
    result = app.invoke(initial.model_dump())
    return TrainingState.model_validate(result)
