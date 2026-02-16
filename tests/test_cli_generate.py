from __future__ import annotations

import json
from pathlib import Path
import sys

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from training_factory.cli import app


def test_generate_writes_bundle_offline(tmp_path) -> None:
    runner = CliRunner()
    out_path = tmp_path / "bundle.json"

    result = runner.invoke(
        app,
        [
            "generate",
            "--topic",
            "Intro to Python",
            "--audience",
            "novice",
            "--out",
            str(out_path),
            "--offline",
        ],
    )

    assert result.exit_code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["request"]["topic"] == "Intro to Python"
    assert "curriculum" in payload
    assert "slides" in payload
    assert "qa" in payload

    assert f"Wrote bundle to {out_path}" in result.stdout
    assert "Topic: Intro to Python" in result.stdout
