from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.brief import generate_brief
from training_factory.agents.curriculum import generate_curriculum
from training_factory.agents.qa import generate_qa
from training_factory.agents.research import generate_research


def _slides_stub() -> dict:
    return {
        "deck": [
            {
                "slide": 1,
                "title": "Lab setup and governance",
                "bullets": [
                    "Complete the hands-on lab exercise",
                    "Use checkpoints to validate outcomes",
                ],
            }
        ]
    }


def _lab_stub() -> dict:
    return {
        "steps": [
            {"step": 1, "instruction": "Create a report workspace"},
            {"step": 2, "instruction": "Configure governance settings"},
        ],
        "checkpoints": ["Workspace created", "Settings configured"],
    }


def _templates_stub() -> dict:
    return {
        "readme_md": {
            "content": "# README\n\nThis lab and slide deck guide learners through module execution."
        },
        "runbook_md": {
            "content": "# RUNBOOK\n\nFollow lab checkpoints and slide/module sequencing."
        },
    }


def _get_check_answer(qa: dict, prompt: str) -> str:
    for item in qa.get("checks", []):
        if isinstance(item, dict) and item.get("prompt") == prompt:
            return str(item.get("answer", ""))
    return ""


def test_qa_grounding_checks_yes_for_valid_curriculum_citations() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = generate_research(request)
    brief = generate_brief(request, research)
    curriculum = generate_curriculum(brief, research)

    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, research)

    assert (
        _get_check_answer(
            qa,
            "Does curriculum include references_used and are they valid research source IDs?",
        )
        == "Yes"
    )
    assert (
        _get_check_answer(
            qa,
            "Does each curriculum module include sources and are they valid research source IDs?",
        )
        == "Yes"
    )


def test_qa_grounding_checks_no_for_invalid_curriculum_citations() -> None:
    request = {"topic": "Power BI basics", "audience": "novice"}
    research = generate_research(request)
    brief = generate_brief(request, research)
    curriculum = generate_curriculum(brief, research)

    bad_curriculum = dict(curriculum)
    bad_curriculum["references_used"] = ["src_DOES_NOT_EXIST"]
    modules = []
    for module in curriculum.get("modules", []):
        if isinstance(module, dict):
            module_copy = dict(module)
            module_copy["sources"] = ["src_DOES_NOT_EXIST"]
            modules.append(module_copy)
    bad_curriculum["modules"] = modules

    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), bad_curriculum, research)

    refs_answer = _get_check_answer(
        qa,
        "Does curriculum include references_used and are they valid research source IDs?",
    )
    modules_answer = _get_check_answer(
        qa,
        "Does each curriculum module include sources and are they valid research source IDs?",
    )

    assert refs_answer == "No" or modules_answer == "No"
    assert qa.get("status") == "fail" or refs_answer == "No" or modules_answer == "No"
