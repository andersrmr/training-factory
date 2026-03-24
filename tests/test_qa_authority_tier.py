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
        "references_used": ["src_002", "src_004"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_002"]}],
    }
    qa = generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())
    assert _authority_answer(qa) == "Yes"


def test_qa_normalization_forces_fail_when_any_check_is_no(monkeypatch) -> None:
    import training_factory.agents.qa as qa_module

    def fake_generate_structured_output(*, normalize, **_kwargs):
        return normalize(
            {
                "status": "pass",
                "checks": [
                    {"prompt": "Do slides align with curriculum/lab objectives?", "answer": "Yes"},
                    {"prompt": "Do templates align with slides and lab?", "answer": "No"},
                ],
            }
        )

    monkeypatch.setattr(qa_module, "generate_structured_output", fake_generate_structured_output)

    curriculum = {
        "topic": "Power BI basics",
        "references_used": ["src_002", "src_004"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_002"]}],
    }
    qa = qa_module.generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())

    assert qa["status"] == "fail"


def test_qa_normalization_converts_pass_fail_answers_to_yes_no(monkeypatch) -> None:
    import training_factory.agents.qa as qa_module

    def fake_generate_structured_output(*, normalize, **_kwargs):
        return normalize(
            {
                "status": "pass",
                "checks": [
                    {"prompt": "Do slides align with curriculum/lab objectives?", "answer": "pass"},
                    {"prompt": "Do slides reference the lab appropriately?", "answer": "passed"},
                ],
            }
        )

    monkeypatch.setattr(qa_module, "generate_structured_output", fake_generate_structured_output)

    curriculum = {
        "topic": "Power BI basics",
        "references_used": ["src_002", "src_004"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_002"]}],
    }
    qa = qa_module.generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())

    assert qa["status"] == "pass"
    semantic_answers = {
        item["prompt"]: item["answer"]
        for item in qa["checks"]
        if item["prompt"] in {
            "Do slides align with curriculum/lab objectives?",
            "Do slides reference the lab appropriately?",
        }
    }
    assert semantic_answers == {
        "Do slides align with curriculum/lab objectives?": "Yes",
        "Do slides reference the lab appropriately?": "Yes",
    }


def test_qa_deterministic_authority_check_overrides_bad_model_answer(monkeypatch) -> None:
    import training_factory.agents.qa as qa_module

    def fake_generate_structured_output(*, normalize, **_kwargs):
        return normalize(
            {
                "status": "pass",
                "checks": [
                    {"prompt": "Do slides align with curriculum/lab objectives?", "answer": "Yes"},
                    {"prompt": "Do slides reference the lab appropriately?", "answer": "Yes"},
                    {
                        "prompt": "Does curriculum cite sufficiently authoritative sources (Tier A/B) for this topic?",
                        "answer": "No",
                    },
                ],
            }
        )

    monkeypatch.setattr(qa_module, "generate_structured_output", fake_generate_structured_output)

    curriculum = {
        "topic": "Power BI governance basics",
        "references_used": ["src_001"],
        "modules": [{"title": "M1", "duration_minutes": 10, "sources": ["src_001"]}],
    }
    qa = qa_module.generate_qa(_slides_stub(), _lab_stub(), _templates_stub(), curriculum, _research_stub())

    assert _authority_answer(qa) == "Yes"
