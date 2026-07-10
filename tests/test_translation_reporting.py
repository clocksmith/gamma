"""Focused tests for deterministic translation reporting artifacts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


_SWEEP_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "run_stage_b_checkpoint_sweep.py"
)
_SPEC = importlib.util.spec_from_file_location("run_stage_b_checkpoint_sweep", _SWEEP_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SWEEP = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SWEEP
_SPEC.loader.exec_module(_SWEEP)

_MATRIX_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "run_stage_a_cpu_matrix.py"
)
_MATRIX_SPEC = importlib.util.spec_from_file_location("run_stage_a_cpu_matrix", _MATRIX_PATH)
assert _MATRIX_SPEC is not None and _MATRIX_SPEC.loader is not None
_MATRIX = importlib.util.module_from_spec(_MATRIX_SPEC)
sys.modules[_MATRIX_SPEC.name] = _MATRIX
_MATRIX_SPEC.loader.exec_module(_MATRIX)


class TranslationScoreboardTests(unittest.TestCase):
    def test_decode_label_captures_beam_policy(self) -> None:
        self.assertEqual(_SWEEP._decode_label("greedy", 1, 1.0), "greedy")
        self.assertEqual(_SWEEP._decode_label("beam", 2, 0.8), "beam2_lp0p8")
        self.assertEqual(_SWEEP._decode_label("beam", 4, 1.25), "beam4_lp1p25")
        self.assertEqual(
            _SWEEP._decode_label("sampled", 1, 1.0, 8, 0.6, 0.9, "mbr_chrf"),
            "sample8_t0p6_p0p9_mbrchrf",
        )

    def test_decode_label_rejects_inconsistent_beam_count(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "greedy requires"):
            _SWEEP._decode_label("greedy", 2, 1.0)
        with self.assertRaisesRegex(RuntimeError, "beam requires"):
            _SWEEP._decode_label("beam", 1, 1.0)
        with self.assertRaisesRegex(RuntimeError, "sampled requires"):
            _SWEEP._decode_label("sampled", 1, 1.0, 1, 0.6, 0.9, "mbr_chrf")

    def test_unchanged_scoreboard_keeps_original_timestamp(self) -> None:
        row = {
            "checkpoint_name": "checkpoint-000100",
            "checkpoint_step": 100,
            "compare_summary": "compare_eval_summary.json",
            "decode": "greedy",
            "duration_s": 1.0,
            "eval_name": "eval2_external",
            "log_path": "eval.log",
            "pairs": "pairs.jsonl",
            "samples": 128,
            "scoreboard_title": "Stage A Checkpoint Evaluation Scoreboard",
            "status": 0,
            "bleu": 33.5,
            "chrf": 60.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "sweep"
            with patch.object(_SWEEP, "_now_utc", return_value="2026-07-10 01:00:00 UTC"):
                _SWEEP._write_scoreboard(
                    out_dir,
                    [row],
                    root,
                    root / "run",
                    "greedy",
                    [("eval2_external", root / "pairs.jsonl")],
                )

            scoreboard = out_dir / "scoreboard.md"
            original = scoreboard.read_text(encoding="utf-8")
            self.assertTrue(original.startswith("# Stage A Checkpoint Evaluation Scoreboard\n"))
            with patch.object(_SWEEP, "_now_utc", return_value="2026-07-10 02:00:00 UTC"):
                _SWEEP._write_scoreboard(
                    out_dir,
                    [row],
                    root,
                    root / "run",
                    "greedy",
                    [("eval2_external", root / "pairs.jsonl")],
                )

            self.assertEqual(scoreboard.read_text(encoding="utf-8"), original)

    def test_unchanged_live_eval_scoreboard_keeps_original_timestamp(self) -> None:
        row = {
            "checkpoint_name": "checkpoint-000100",
            "checkpoint_step": 100,
            "compare_summary": "compare_eval_summary.json",
            "duration_s": 1.0,
            "log_path": "eval.log",
            "pairs": "pairs.jsonl",
            "samples": 128,
            "status": 0,
            "bleu": 33.5,
            "chrf": 60.0,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "live_eval"
            with patch.object(_MATRIX, "_now_utc", return_value="2026-07-10 01:00:00 UTC"):
                _MATRIX._write_live_eval_artifacts(
                    out_dir,
                    [row],
                    repo_root=root,
                    run_root=root / "run",
                    eval_pairs=root / "eval2_external",
                )

            scoreboard = out_dir / "scoreboard.md"
            original = scoreboard.read_text(encoding="utf-8")
            with patch.object(_MATRIX, "_now_utc", return_value="2026-07-10 02:00:00 UTC"):
                _MATRIX._write_live_eval_artifacts(
                    out_dir,
                    [row],
                    repo_root=root,
                    run_root=root / "run",
                    eval_pairs=root / "eval2_external",
                )

            self.assertEqual(scoreboard.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
