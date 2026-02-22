from __future__ import annotations

import os
from importlib import import_module
from pathlib import Path
import sys
from typing import Generator

import pytest

os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGSMITH_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING_SAMPLING_RATE"] = "0"
os.environ["LANGSMITH_TRACING_SAMPLING_RATE"] = "0"
os.environ.pop("LANGSMITH_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _clear_settings_cache() -> None:
    settings_module = import_module("training_factory.settings")
    settings_module.get_settings.cache_clear()


@pytest.fixture(autouse=True)
def force_offline_mode(monkeypatch) -> Generator[None, None, None]:
    monkeypatch.setenv("TRAINING_FACTORY_OFFLINE", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-should-not-be-used")
    _clear_settings_cache()
    yield
    _clear_settings_cache()
