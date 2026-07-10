"""Focused tests for aligned translation candidate-pool construction."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "build_translation_candidate_pool.py"
)
_SPEC = importlib.util.spec_from_file_location("build_translation_candidate_pool", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_POOL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _POOL
_SPEC.loader.exec_module(_POOL)


def _row(prediction: str, source: str = "hola") -> dict[str, str]:
    return {
        "pair": "es-en",
        "src_lang": "es",
        "tgt_lang": "en",
        "source": source,
        "target_pos": "hello",
        "pred": prediction,
    }


class TranslationCandidatePoolTests(unittest.TestCase):
    def test_merge_rows_preserves_labels_and_order(self) -> None:
        rows = _POOL._merge_rows([("current", [_row("hello")]), ("specialist", [_row("hi")])])

        self.assertEqual(rows[0]["candidates"], ["hello", "hi"])
        self.assertEqual(rows[0]["candidate_sources"], ["current", "specialist"])
        self.assertEqual(rows[0]["pred"], "hello")

    def test_merge_rows_rejects_alignment_mismatch(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "alignment mismatch"):
            _POOL._merge_rows([("current", [_row("hello")]), ("specialist", [_row("hi", "adios")])])


if __name__ == "__main__":
    unittest.main()
