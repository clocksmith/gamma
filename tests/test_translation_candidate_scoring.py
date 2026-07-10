"""Focused tests for translation candidate conditional scoring."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys
import unittest

import torch


_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "score_translation_candidates.py"
)
_SPEC = importlib.util.spec_from_file_location("score_translation_candidates", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SCORER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SCORER
_SPEC.loader.exec_module(_SCORER)


class TranslationCandidateScoringTests(unittest.TestCase):
    def test_score_key_validation(self) -> None:
        self.assertEqual(_SCORER._validated_score_key("specialist_scores"), "specialist_scores")
        with self.assertRaisesRegex(RuntimeError, "Invalid --score-key"):
            _SCORER._validated_score_key("bad-key")

    def test_longest_common_prefix(self) -> None:
        self.assertEqual(_SCORER._longest_common_prefix([1, 2, 3], [1, 2, 4]), 2)
        self.assertEqual(_SCORER._longest_common_prefix([], [1, 2]), 0)

    def test_target_logprob_scores_respect_left_padding_and_boundary(self) -> None:
        input_ids = torch.tensor([[1, 2, 3, 4], [0, 0, 2, 3]])
        logits = torch.zeros((2, 4, 5))

        scores = _SCORER._target_logprob_scores(
            logits,
            input_ids,
            raw_lengths=[4, 2],
            target_starts=[2, 1],
        )

        self.assertEqual(scores[0]["token_count"], 2)
        self.assertEqual(scores[1]["token_count"], 1)
        self.assertAlmostEqual(float(scores[0]["mean_logprob"]), -math.log(5), places=6)
        self.assertAlmostEqual(float(scores[1]["mean_logprob"]), -math.log(5), places=6)


if __name__ == "__main__":
    unittest.main()
