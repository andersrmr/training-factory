from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.utils.json_extract import extract_json_object


def test_extract_json_object_plain() -> None:
    raw = '{"status": "pass", "checks": []}'
    assert extract_json_object(raw) == {"status": "pass", "checks": []}


def test_extract_json_object_fenced() -> None:
    raw = """```json
{"status": "pass", "checks": []}
```"""
    assert extract_json_object(raw) == {"status": "pass", "checks": []}


def test_extract_json_object_with_prose_wrapper() -> None:
    raw = 'Here is the output: {"status": "fail", "checks": []} Thanks.'
    assert extract_json_object(raw) == {"status": "fail", "checks": []}


def test_extract_json_object_rejects_non_object() -> None:
    with pytest.raises(ValueError, match="Expected a JSON object"):
        extract_json_object("[1, 2, 3]")


def test_extract_json_object_missing_json() -> None:
    with pytest.raises(ValueError, match="No JSON object found"):
        extract_json_object("not json")
