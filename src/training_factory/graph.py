from pathlib import Path
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from training_factory.agents.brief import generate_brief
from training_factory.agents.curriculum import generate_curriculum
from training_factory.agents.lab import generate_lab
from training_factory.agents.qa import generate_qa
from training_factory.agents.research import generate_research
from training_factory.agents.research_qa import generate_research_qa
from training_factory.agents.slides import generate_slides
from training_factory.agents.templates import generate_templates
from training_factory.state import TrainingState
from training_factory.utils.json_schema import validate_json

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT_DIR / "schemas"


class GraphState(TypedDict):
    request: dict[str, Any]
    research: dict[str, Any]
    research_qa: dict[str, Any]
    brief: dict[str, Any]
    curriculum: dict[str, Any]
    lab: dict[str, Any]
    slides: dict[str, Any]
    templates: dict[str, Any]
    qa: dict[str, Any]
    packaging: dict[str, Any]
    research_revision_count: int
    revision_count: int


def _research_node(state: GraphState) -> dict[str, Any]:
    research = generate_research(state["request"])
    return {"research": research}


def _brief_node(state: GraphState) -> dict[str, Any]:
    brief = generate_brief(state["request"], state.get("research", {}))
    return {"brief": brief}


def _research_qa_node(state: GraphState) -> dict[str, Any]:
    research_qa = generate_research_qa(state.get("research", {}), state["request"])
    return {"research_qa": research_qa}


def _research_retry_node(state: GraphState) -> dict[str, Any]:
    revision_count = int(state.get("research_revision_count", 0))
    # Retry bookkeeping only: keep research/research_qa payloads unchanged here.
    return {"research_revision_count": revision_count + 1}


def _curriculum_node(state: GraphState) -> dict[str, Any]:
    curriculum = generate_curriculum(state["brief"], state["research"])
    return {"curriculum": curriculum}


def _slides_node(state: GraphState) -> dict[str, Any]:
    slides = generate_slides(state["curriculum"])
    qa_status = state.get("qa", {}).get("status")
    revision_count = int(state.get("revision_count", 0))
    if qa_status == "fail" and revision_count < 1:
        return {"slides": slides, "revision_count": revision_count + 1}
    return {"slides": slides}


def _lab_node(state: GraphState) -> dict[str, Any]:
    lab = generate_lab(state["curriculum"])
    return {"lab": lab}


def _templates_node(state: GraphState) -> dict[str, Any]:
    templates = generate_templates(state["slides"])
    return {"templates": templates}


def _qa_node(state: GraphState) -> dict[str, Any]:
    qa = generate_qa(state["slides"], state["lab"], state["templates"])
    return {"qa": qa}


def _route_after_qa(state: GraphState) -> str:
    qa_status = state.get("qa", {}).get("status")
    revision_count = int(state.get("revision_count", 0))
    if qa_status == "fail" and revision_count < 1:
        return "slides"
    return "package"


def _route_after_research_qa(state: GraphState) -> str:
    research_qa_status = state.get("research_qa", {}).get("status")
    revision_count = int(state.get("research_revision_count", 0))
    if research_qa_status == "fail" and revision_count < 1:
        return "research_retry"
    return "brief"


def _canonicalize_lab_for_bundle(lab: dict[str, Any]) -> dict[str, Any]:
    if isinstance(lab.get("labs"), list):
        return lab

    if all(key in lab for key in ("title", "objective", "steps")):
        steps = lab.get("steps", [])
        instructions = []
        if isinstance(steps, list):
            instructions = [
                step.get("instruction", "")
                for step in steps
                if isinstance(step, dict) and isinstance(step.get("instruction"), str)
            ]
        if not instructions:
            instructions = ["Complete the lab"]
        return {
            "labs": [
                {
                    "title": lab.get("title", "Lab"),
                    "instructions": instructions,
                    "expected_outcome": lab.get("objective", "Lab objective met"),
                }
            ]
        }
    return {"labs": []}


def _canonicalize_templates_for_bundle(
    templates: dict[str, Any],
) -> dict[str, dict[str, str]]:
    readme_content = ""
    runbook_content = ""

    readme_node = templates.get("readme_md")
    runbook_node = templates.get("runbook_md")
    if isinstance(readme_node, dict) and isinstance(readme_node.get("content"), str):
        readme_content = readme_node["content"]
    elif isinstance(templates.get("README.md"), str):
        readme_content = templates["README.md"]

    if isinstance(runbook_node, dict) and isinstance(runbook_node.get("content"), str):
        runbook_content = runbook_node["content"]
    elif isinstance(templates.get("RUNBOOK.md"), str):
        runbook_content = templates["RUNBOOK.md"]

    return {
        "readme_md": {"content": readme_content},
        "runbook_md": {"content": runbook_content},
    }


def _package_node(state: GraphState) -> dict[str, Any]:
    lab = _canonicalize_lab_for_bundle(state["lab"])
    templates = _canonicalize_templates_for_bundle(state["templates"])
    packaging = {
        "request": state["request"],
        "research": state["research"],
        "research_qa": state["research_qa"],
        "brief": state["brief"],
        "curriculum": state["curriculum"],
        "lab": lab,
        "slides": state["slides"],
        "templates": templates,
        "qa": state["qa"],
    }
    validate_json(packaging, SCHEMA_DIR / "bundle.schema.json")
    return {
        "packaging": packaging,
        "revision_count": int(state.get("revision_count", 0)),
    }


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("research", _research_node)
    graph.add_node("research_qa", _research_qa_node)
    graph.add_node("research_retry", _research_retry_node)
    graph.add_node("brief", _brief_node)
    graph.add_node("curriculum", _curriculum_node)
    graph.add_node("slides", _slides_node)
    graph.add_node("lab", _lab_node)
    graph.add_node("templates", _templates_node)
    graph.add_node("qa", _qa_node)
    graph.add_node("package", _package_node)

    graph.add_edge(START, "research")
    graph.add_edge("research", "research_qa")
    graph.add_conditional_edges(
        "research_qa",
        _route_after_research_qa,
        {"research_retry": "research_retry", "brief": "brief"},
    )
    graph.add_edge("research_retry", "research")
    graph.add_edge("brief", "curriculum")
    graph.add_edge("curriculum", "slides")
    graph.add_edge("slides", "lab")
    graph.add_edge("lab", "templates")
    graph.add_edge("templates", "qa")
    graph.add_conditional_edges(
        "qa",
        _route_after_qa,
        {"slides": "slides", "package": "package"},
    )
    graph.add_edge("package", END)

    return graph.compile()


def run_pipeline(
    topic: str,
    audience: str,
    *,
    research: dict[str, Any] | None = None,
) -> TrainingState:
    app = build_graph()
    request: dict[str, Any] = {"topic": topic, "audience": audience}
    if research is not None:
        request["research"] = research
    initial = TrainingState(request=request)
    result = app.invoke(cast(GraphState, initial.model_dump()))
    return TrainingState.model_validate(result)
