"""Focused tests for the reference-free translation candidate selector."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


_SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "select_translation_candidates.py"
)
_SPEC = importlib.util.spec_from_file_location("select_translation_candidates", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_SELECTOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SELECTOR
_SPEC.loader.exec_module(_SELECTOR)


def _row(gap: float, reference: str = "the selected translation") -> dict[str, object]:
    return {
        "pair": "es-en",
        "src_lang": "es",
        "tgt_lang": "en",
        "source": "la traduccion 12",
        "target_pos": reference,
        "pred": "the current translation",
        "candidates": ["the current translation", "the selected translation"],
        "candidate_sources": ["current", "specialist"],
        "current_model_scores": [
            {"mean_logprob": -0.2, "sum_logprob": -2.0, "token_count": 10},
            {"mean_logprob": -0.2 + gap, "sum_logprob": -2.0, "token_count": 10},
        ],
        "specialist_model_scores": [
            {"mean_logprob": -0.3, "sum_logprob": -3.0, "token_count": 10},
            {"mean_logprob": -0.3 + gap, "sum_logprob": -3.0, "token_count": 10},
        ],
    }


class TranslationCandidateSelectorTests(unittest.TestCase):
    def test_features_do_not_read_training_reference(self) -> None:
        first = _row(0.1, reference="first reference")
        second = _row(0.1, reference="completely different reference")

        self.assertEqual(
            _SELECTOR._feature_vector(first, _SELECTOR.DEFAULT_SCORE_KEYS),
            _SELECTOR._feature_vector(second, _SELECTOR.DEFAULT_SCORE_KEYS),
        )

    def test_ridge_predicts_feature_correlated_delta(self) -> None:
        features = [[-2.0], [-1.0], [1.0], [2.0]]
        targets = [-4.0, -2.0, 2.0, 4.0]
        model = _SELECTOR._fit_ridge(features, targets, regularization=0.0)

        predictions = _SELECTOR._predict(model, [[-3.0], [3.0]])

        self.assertLess(predictions[0], 0.0)
        self.assertGreater(predictions[1], 0.0)

    def test_weighted_logistic_predicts_feature_correlated_choice(self) -> None:
        features = [[-2.0], [-1.0], [1.0], [2.0]]
        targets = [-4.0, -2.0, 2.0, 4.0]
        model = _SELECTOR._fit_weighted_logistic(features, targets, regularization=0.1)

        predictions = _SELECTOR._predict(model, [[-3.0], [3.0]])

        self.assertLess(predictions[0], 0.0)
        self.assertGreater(predictions[1], 0.0)

    def test_mlp_serialized_prediction_matches_network_output(self) -> None:
        features = [[-2.0], [-1.0], [1.0], [2.0]]
        targets = [-4.0, -2.0, 2.0, 4.0]
        model = _SELECTOR._fit_mlp_regression(
            features,
            targets,
            regularization=0.01,
            hidden_size=4,
            epochs=50,
            learning_rate=0.01,
            seed=42,
        )

        predictions = _SELECTOR._predict(model, [[-3.0], [3.0]])

        self.assertLess(predictions[0], predictions[1])

    def test_unanimous_ensemble_requires_all_specialist_votes(self) -> None:
        predictions = [[1.0, 1.0, -1.0], [1.0, -1.0, -1.0], [0.5, 2.0, -1.0]]

        choices = _SELECTOR._ensemble_choices(predictions, "unanimous_specialist")

        self.assertEqual(choices, [1, 0, 0])

    def test_numeric_error_delta_rewards_number_preservation(self) -> None:
        row = _row(0.0)
        row["candidates"] = ["the translation", "the translation 12"]

        features = _SELECTOR._feature_vector(row, _SELECTOR.DEFAULT_SCORE_KEYS)
        names = _SELECTOR._feature_names(_SELECTOR.DEFAULT_SCORE_KEYS)

        self.assertGreater(features[names.index("numeric_error_delta")], 0.0)

    def test_quadratic_feature_expansion_matches_names(self) -> None:
        values = [2.0, 3.0]
        names = ["first", "second"]

        expanded = _SELECTOR._expand_feature_vector(values, "quadratic")
        expanded_names = _SELECTOR._expanded_feature_names(names, "quadratic")

        self.assertEqual(expanded, [2.0, 3.0, 4.0, 9.0, 6.0])
        self.assertEqual(expanded_names, ["first", "second", "first^2", "second^2", "first*second"])

    def test_fold_assignment_keeps_duplicate_sources_together(self) -> None:
        rows = [_row(float(index)) for index in range(10)]
        for index, row in enumerate(rows):
            row["source"] = f"source {index // 2}"

        assignments = _SELECTOR._fold_assignments(rows, folds=2, seed=42)

        for index in range(0, len(rows), 2):
            self.assertEqual(assignments[index], assignments[index + 1])

    def test_training_inputs_reject_duplicate_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "first.jsonl"
            second = Path(temp_dir) / "second.jsonl"
            payload = json.dumps(_row(0.1)) + "\n"
            first.write_text(payload, encoding="utf-8")
            second.write_text(payload, encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "Duplicate training row"):
                _SELECTOR._load_training_rows([first, second])


if __name__ == "__main__":
    unittest.main()
