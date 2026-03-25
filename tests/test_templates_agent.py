from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _clear_settings_cache() -> None:
    settings_module = import_module("training_factory.settings")
    settings_module.get_settings.cache_clear()


def test_generate_templates_falls_back_when_structured_content_is_not_string(monkeypatch) -> None:
    monkeypatch.setenv("TRAINING_FACTORY_OFFLINE", "0")
    monkeypatch.setenv("TEST_MODE", "0")
    _clear_settings_cache()

    from training_factory import llm
    from training_factory.agents.templates import generate_templates

    def _bad_templates_response(*, prompt: str, fallback_text: str) -> str:
        return (
            '{"readme_md":{"filename":"README.md","content":"# Training Bundle\\n\\nThis markdown stays valid because it includes enough detail to satisfy schema length requirements."},'
            '"runbook_md":{"filename":"RUNBOOK.md","content":{"lab":"Version Control Fundamentals"}}}'
        )

    monkeypatch.setattr(llm, "invoke_text", _bad_templates_response)

    result = generate_templates({"deck": [{"title": "Version Control Fundamentals", "bullets": ["Lab walkthrough"]}]})

    assert result["readme_md"]["content"].startswith(
        "# Training Bundle\n\nThis markdown stays valid because it includes enough detail to satisfy schema length requirements."
    )
    assert "Version Control Fundamentals" in result["readme_md"]["content"]
    assert isinstance(result["runbook_md"]["content"], str)
    assert result["runbook_md"]["filename"] == "RUNBOOK.md"
    assert "Review the slide deck for Version Control Fundamentals" in result["runbook_md"]["content"]

    _clear_settings_cache()


def test_generate_templates_appends_slide_and_lab_alignment_when_model_is_generic(monkeypatch) -> None:
    monkeypatch.setenv("TRAINING_FACTORY_OFFLINE", "0")
    monkeypatch.setenv("TEST_MODE", "0")
    _clear_settings_cache()

    from training_factory import llm
    from training_factory.agents.templates import generate_templates

    def _generic_templates_response(*, prompt: str, fallback_text: str) -> str:
        return (
            '{"readme_md":{"filename":"README.md","content":"# README\\n\\nUse this training bundle during delivery."},'
            '"runbook_md":{"filename":"RUNBOOK.md","content":"# RUNBOOK\\n\\nReview the materials and guide learners through the session."}}'
        )

    monkeypatch.setattr(llm, "invoke_text", _generic_templates_response)

    result = generate_templates({"deck": [{"title": "Workspace Governance", "bullets": ["Hands-on lab checkpoint"]}]})

    readme = result["readme_md"]["content"].lower()
    runbook = result["runbook_md"]["content"].lower()
    assert "workspace governance" in readme
    assert "lab" in readme
    assert "slide deck" in readme
    assert "workspace governance" in runbook
    assert "checkpoint" in runbook

    _clear_settings_cache()
