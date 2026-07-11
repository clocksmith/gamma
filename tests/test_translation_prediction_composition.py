"""Focused tests for aligned directional prediction composition."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "compose_translation_predictions.py"
)
_SPEC = importlib.util.spec_from_file_location("compose_translation_predictions", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_COMPOSER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _COMPOSER
_SPEC.loader.exec_module(_COMPOSER)


def _row(pair: str, source: str, prediction: str) -> dict[str, str]:
    source_lang, target_lang = pair.split("-")
    return {
        "pair": pair,
        "src_lang": source_lang,
        "tgt_lang": target_lang,
        "source": source,
        "target_pos": f"reference {source}",
        "pred": prediction,
    }


class TranslationPredictionCompositionTests(unittest.TestCase):
    def test_composition_preserves_order_and_replaces_matches(self) -> None:
        base = [_row("en-es", "one", "base one"), _row("es-en", "two", "base two")]
        override = [_row("es-en", "two", "selected two")]

        output, counts = _COMPOSER._compose_rows(base, override)

        self.assertEqual([row["source"] for row in output], ["one", "two"])
        self.assertEqual([row["pred"] for row in output], ["base one", "selected two"])
        self.assertEqual(counts["base"], 1)
        self.assertEqual(counts["override"], 1)

    def test_composition_rejects_unknown_override(self) -> None:
        base = [_row("en-es", "one", "base one")]
        override = [_row("es-en", "missing", "selected")]

        with self.assertRaisesRegex(RuntimeError, "did not match"):
            _COMPOSER._compose_rows(base, override)

    def test_main_records_the_selected_routing_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_path = root / "base.jsonl"
            override_path = root / "override.jsonl"
            out_dir = root / "out"
            base_path.write_text(json.dumps(_row("es-en", "one", "base")) + "\n", encoding="utf-8")
            override_path.write_text(json.dumps(_row("es-en", "one", "selected")) + "\n", encoding="utf-8")
            args = argparse.Namespace(
                base=str(base_path),
                override=str(override_path),
                teacher_predictions="",
                out_dir=str(out_dir),
                model_id="student",
                teacher_model_id="teacher",
                eval_dataset_path="eval.jsonl",
                candidate_selection="reference_free_mlp_selector",
            )

            with patch.object(_COMPOSER, "_parse_args", return_value=args):
                self.assertEqual(_COMPOSER.main(), 0)

            student = json.loads((out_dir / "student_eval_summary.json").read_text(encoding="utf-8"))
            compare = json.loads((out_dir / "compare_eval_summary.json").read_text(encoding="utf-8"))
            composition = json.loads((out_dir / "composition_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(student["candidate_selection"], "reference_free_mlp_selector")
            self.assertEqual(compare["decode_metadata"]["candidate_selection"], "reference_free_mlp_selector")
            self.assertEqual(composition["candidate_selection"], "reference_free_mlp_selector")


if __name__ == "__main__":
    unittest.main()
