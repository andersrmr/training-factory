from __future__ import annotations

from importlib import import_module
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _clear_settings_cache() -> None:
    settings_module = import_module("training_factory.settings")
    settings_module.get_settings.cache_clear()


def test_generate_slides_injects_lab_reference_when_model_omits_it(monkeypatch) -> None:
    monkeypatch.setenv("TRAINING_FACTORY_OFFLINE", "0")
    monkeypatch.setenv("TEST_MODE", "0")
    _clear_settings_cache()

    from training_factory import llm
    from training_factory.agents.slides import generate_slides

    def _generic_slides_response(*, prompt: str, fallback_text: str) -> str:
        return (
            '{"deck":[{"slide":1,"title":"Workspace Governance",'
            '"bullets":["Define workspace governance responsibilities.",'
            '"Explain deployment roles and approvals.",'
            '"Compare governance tradeoffs across environments.",'
            '"Review an example governance workflow."]}]}'
        )

    monkeypatch.setattr(llm, "invoke_text", _generic_slides_response)

    result = generate_slides({"modules": [{"title": "Workspace Governance"}]})

    bullets = result["deck"][0]["bullets"]
    assert len(bullets) == 4
    assert any(token in bullets[-1].lower() for token in ("lab", "exercise", "checkpoint", "hands-on"))

    _clear_settings_cache()
