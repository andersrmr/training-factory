from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.agents.qa import generate_qa

AUTHORITY_PROMPT = "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?"


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


def _aligned_templates_stub() -> dict:
    return {
        "readme_md": {
            "content": "# README\n\nThis Lab setup and governance module includes the hands-on lab exercise."
        },
        "runbook_md": {
            "content": "# RUNBOOK\n\nUse the slide deck, module flow, and checkpoint-based lab sequence for Lab setup and governance."
        },
    }


def _research_stub() -> dict:
    return {
        "sources": [
            {"id": "src_001", "authority_tier": "A"},
            {"id": "src_002", "authority_tier": "B"},
            {"id": "src_004", "authority_tier": "B"},
            {"id": "src_003", "authority_tier": "C"},
        ]
    }


def _authority_answer(qa: dict) -> str:
    for item in qa.get("checks", []):
        if isinstance(item, dict) and item.get("prompt") == AUTHORITY_PROMPT:
            return str(item.get("answer", ""))
    return ""


def test_qa_authority_check_sensitive_topic_fails_with_only_tier_c() -> None:
    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_003"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_003"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())
    assert _authority_answer(qa) == "No"


def test_qa_authority_check_sensitive_topic_passes_with_tier_a() -> None:
    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_001"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())
    assert _authority_answer(qa) == "Yes"


def test_qa_authority_check_non_sensitive_topic_passes_with_two_tier_b() -> None:
    curriculum = {
        "topic": "Power BI basics",
        "references_used": ["src_001"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())
    assert _authority_answer(qa) == "Yes"


def test_qa_status_is_pass_when_all_deterministic_checks_pass() -> None:
    curriculum = {
        "topic": "Lab setup and governance",
        "references_used": ["src_001"],
        "modules": [{"title": "Lab setup and governance", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _aligned_templates_stub(), curriculum, _research_stub())

    assert qa["status"] == "pass"


def test_slides_alignment_requires_overlap_with_curriculum_module_titles() -> None:
    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_001"],
        "modules": [{"title": "Lab setup and governance", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _aligned_templates_stub(), curriculum, _research_stub())

    answers = {item["prompt"]: item["answer"] for item in qa["checks"]}
    assert answers["Do slides align with curriculum/lab objectives?"] == "Yes"


def test_slides_alignment_fails_without_curriculum_title_overlap() -> None:
    curriculum = {
        "topic": "Power BI lifecycle management",
        "references_used": ["src_001"],
        "modules": [
            {
                "title": "Lifecycle deployment governance",
                "duration_minutes": 10,
                "sources": ["src_001"],
            }
        ],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _aligned_templates_stub(), curriculum, _research_stub())

    answers = {item["prompt"]: item["answer"] for item in qa["checks"]}
    assert answers["Do slides align with curriculum/lab objectives?"] == "No"


def test_templates_alignment_requires_slide_and_lab_language_with_title_overlap() -> None:
    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_001"],
        "modules": [{"title": "Workspace Governance", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    slides = {
        "deck": [
            {
                "slide": 1,
                "title": "Workspace Governance",
                "bullets": [
                    "Complete the lab exercise for workspace governance",
                    "Use checkpoints to validate outcomes",
                ],
            }
        ]
    }
    templates = {
        "readme_md": {
            "content": "# README\n\nThis module covers Workspace Governance and the hands-on lab exercise."
        },
        "runbook_md": {
            "content": "# RUNBOOK\n\nFollow the slide deck, module sequence, and checkpoint-based lab flow."
        },
    }

    qa = generate_qa(slides, _lab_stub(), templates, curriculum, _research_stub())
    answers = {item["prompt"]: item["answer"] for item in qa["checks"]}
    assert answers["Do templates align with slides and lab?"] == "Yes"


def test_templates_alignment_fails_without_slide_title_overlap() -> None:
    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_001"],
        "modules": [{"title": "Workspace Governance", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    slides = {
        "deck": [
            {
                "slide": 1,
                "title": "Workspace Governance",
                "bullets": [
                    "Complete the lab exercise for workspace governance",
                    "Use checkpoints to validate outcomes",
                ],
            }
        ]
    }
    templates = {
        "readme_md": {
            "content": "# README\n\nThis guide includes the lab exercise and checkpoint flow."
        },
        "runbook_md": {
            "content": "# RUNBOOK\n\nUse the module checklist and lab exercise steps during delivery."
        },
    }

    qa = generate_qa(slides, _lab_stub(), templates, curriculum, _research_stub())
    answers = {item["prompt"]: item["answer"] for item in qa["checks"]}
    assert answers["Do templates align with slides and lab?"] == "No"
