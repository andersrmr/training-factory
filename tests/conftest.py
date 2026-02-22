from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGSMITH_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING_SAMPLING_RATE"] = "0"
os.environ["LANGSMITH_TRACING_SAMPLING_RATE"] = "0"
os.environ.pop("LANGSMITH_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.settings import get_settings


@pytest.fixture(autouse=True)
def force_offline_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRAINING_FACTORY_OFFLINE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-be-used")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
