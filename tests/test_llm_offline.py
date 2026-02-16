from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory import llm


def test_invoke_text_offline_bypasses_model(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("build_chat_model should not be called in offline mode")

    monkeypatch.setattr(llm, "build_chat_model", fail_if_called)
    result = llm.invoke_text(prompt="ignored", fallback_text="offline")
    assert result == "offline"
