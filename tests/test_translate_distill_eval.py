"""Focused tests for translation evaluation controls."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import torch


_EVAL_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "eval"
    / "run_translate_distill_eval.py"
)
_SPEC = importlib.util.spec_from_file_location("run_translate_distill_eval", _EVAL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_EVAL = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _EVAL
_SPEC.loader.exec_module(_EVAL)


class _FakeLoraLayer(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.scaling = {"default": 2.0}

    def scale_layer(self, scale: float) -> None:
        self.scaling["default"] *= scale


class TranslateDistillEvalTests(unittest.TestCase):
    def test_mbr_chrf_selects_consensus_and_breaks_ties_stably(self) -> None:
        selected = _EVAL._select_candidate(
            ["the translation is correct", "the translation is correct", "unrelated output"],
            "mbr_chrf",
        )

        self.assertEqual(selected, 0)

    def test_candidate_selection_rejects_empty_input(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "empty candidate"):
            _EVAL._select_candidate([], "mbr_chrf")

    def test_eval_offset_applies_after_language_filters(self) -> None:
        rows = [
            {"src_lang": "en", "tgt_lang": "es", "pair": "en-es", "source": "zero", "target_pos": "cero", "target_neg": "otro"},
            {"src_lang": "es", "tgt_lang": "en", "pair": "es-en", "source": "uno", "target_pos": "one", "target_neg": "other"},
            {"src_lang": "es", "tgt_lang": "en", "pair": "es-en", "source": "dos", "target_pos": "two", "target_neg": "other"},
            {"src_lang": "es", "tgt_lang": "en", "pair": "es-en", "source": "tres", "target_pos": "three", "target_neg": "other"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pairs.jsonl"
            path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            selected = _EVAL._load_rows(
                [path],
                source_langs={"es"},
                target_langs={"en"},
                max_rows=1,
                row_offset=1,
                allow_compat_mismatch=False,
                allow_partial_contract=True,
            )

        self.assertEqual([row.source for row in selected], ["dos"])

    def test_weight_interpolation_supports_extrapolation(self) -> None:
        base = torch.nn.Linear(2, 1, bias=False)
        tuned = torch.nn.Linear(2, 1, bias=False)
        with torch.no_grad():
            base.weight.fill_(2.0)
            tuned.weight.fill_(4.0)

        _EVAL._interpolate_module_weights(base, tuned, 1.5)

        torch.testing.assert_close(base.weight, torch.full_like(base.weight, 5.0))

    def test_adapter_scale_multiplies_loaded_lora_layers(self) -> None:
        model = torch.nn.Sequential(_FakeLoraLayer(), torch.nn.Linear(2, 2))

        count = _EVAL._scale_lora_adapters(model, 0.25)

        self.assertEqual(count, 1)
        self.assertEqual(model[0].scaling["default"], 0.5)

    def test_adapter_scale_rejects_non_adapter_model(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "no loaded LoRA layers"):
            _EVAL._scale_lora_adapters(torch.nn.Linear(2, 2), 0.5)

    def test_tokenizer_revision_inherits_for_same_repository(self) -> None:
        tokenizer_ref, tokenizer_revision = _EVAL._resolve_tokenizer_identity(
            "example/student",
            "1" * 40,
        )

        self.assertEqual(tokenizer_ref, "example/student")
        self.assertEqual(tokenizer_revision, "1" * 40)

    def test_tokenizer_revision_does_not_cross_repositories(self) -> None:
        tokenizer_ref, tokenizer_revision = _EVAL._resolve_tokenizer_identity(
            "example/student",
            "1" * 40,
            "example/teacher-tokenizer",
        )

        self.assertEqual(tokenizer_ref, "example/teacher-tokenizer")
        self.assertEqual(tokenizer_revision, "")


if __name__ == "__main__":
    unittest.main()
