from __future__ import annotations

import csv
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import scripts.eval_phase_b as eval_phase_b
from training_factory.research.fallback_provider import SimpleFallbackSearchProvider


def test_eval_phase_b_reduced_matrix_writes_summary_and_bundle(monkeypatch) -> None:
    import training_factory.agents.research as research_module

    monkeypatch.setattr(
        research_module,
        "get_search_provider",
        lambda name, web=False: SimpleFallbackSearchProvider(),
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_root = Path(tmp_dir)
        summary_path = eval_phase_b.run_eval(
            out_root=out_root,
            case_ids=["C1"],
            mode_ids=["M1"],
        )

        assert summary_path.exists()

        with summary_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))

        assert len(rows) == 2

        bundle_path = out_root / "C1" / "M1" / "bundle.json"
        assert bundle_path.exists()
