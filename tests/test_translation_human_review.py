"""Tests for the frozen EN/ES blocking human-review evaluator."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import jsonschema


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMOTION_ROOT = REPO_ROOT / "projects" / "distillation" / "translation" / "promotion"
CONTRACT_PATH = PROMOTION_ROOT / "human-review-contract.v1.json"
SCHEMA_PATH = PROMOTION_ROOT / "human-review-contract.schema.json"
EVALUATOR_PATH = (
    REPO_ROOT
    / "projects"
    / "distillation"
    / "translation"
    / "pipeline"
    / "evaluate_translation_human_review.py"
)
_SPEC = importlib.util.spec_from_file_location("evaluate_translation_human_review", EVALUATOR_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_EVALUATOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _EVALUATOR
_SPEC.loader.exec_module(_EVALUATOR)


class TranslationHumanReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_frozen_contract_matches_schema_and_promotion_binding(self) -> None:
        jsonschema.Draft202012Validator(self.schema).validate(self.contract)
        promotion = json.loads((PROMOTION_ROOT / "promotion-contract.v1.json").read_text(encoding="utf-8"))
        self.assertEqual(promotion["humanReview"]["thresholdStatus"], "frozen")
        self.assertEqual(
            promotion["humanReview"]["contractSha256"],
            hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        )

    def test_exact_sign_test_and_holm_adjustment(self) -> None:
        self.assertEqual(_EVALUATOR.exact_one_sided_sign_p(0, 0), 1.0)
        self.assertEqual(_EVALUATOR.exact_one_sided_sign_p(1, 0), 0.5)
        self.assertAlmostEqual(_EVALUATOR.exact_one_sided_sign_p(3, 1), 0.3125)
        adjusted = _EVALUATOR.holm_adjust({"a": 0.01, "b": 0.03, "c": 0.2})
        self.assertEqual(adjusted, {"a": 0.03, "b": 0.06, "c": 0.2})

    def test_complete_stratum_safe_review_passes(self) -> None:
        contract = self._small_contract()
        receipt = _EVALUATOR.evaluate_review(self._passing_ledger(contract), contract)

        self.assertEqual(receipt["status"], "passed")
        self.assertEqual(receipt["blockers"], [])
        self.assertEqual(receipt["population"]["observedDistinctItems"], 60)
        self.assertEqual(receipt["completeness"]["completeAdjudicatedPairs"], 180)

    def test_domain_direction_regression_blocks_even_when_overall_wins(self) -> None:
        contract = self._small_contract()
        ledger = self._passing_ledger(contract)
        comparator = contract["blockingComparators"][0]
        for row in ledger["rows"]:
            if (
                row["comparatorId"] == comparator
                and row["direction"] == "es-en"
                and row["domain"] == "medical_public_health"
            ):
                preference = (
                    "output_b_better"
                    if row["candidateSide"] == "output_a"
                    else "output_a_better"
                )
                for reviewer in row["reviewers"]:
                    reviewer["preference"] = preference
                row["adjudication"]["preference"] = preference

        receipt = _EVALUATOR.evaluate_review(ledger, contract)

        self.assertEqual(receipt["status"], "failed")
        self.assertTrue(
            any(blocker.startswith("human_preference_stratum_regression:") for blocker in receipt["blockers"])
        )

    def test_missing_pair_and_candidate_direction_error_fail_closed(self) -> None:
        contract = self._small_contract()
        ledger = self._passing_ledger(contract)
        ledger["rows"].pop()
        first = ledger["rows"][0]
        error_field = "outputAErrors" if first["candidateSide"] == "output_a" else "outputBErrors"
        first["adjudication"][error_field] = ["direction_contract"]

        receipt = _EVALUATOR.evaluate_review(ledger, contract)

        self.assertEqual(receipt["status"], "failed")
        self.assertIn("item_comparator_matrix_incomplete", receipt["blockers"])
        self.assertIn("candidate_direction_contract_error_present", receipt["blockers"])

    def test_candidate_output_and_error_labels_must_match_across_comparators(self) -> None:
        contract = self._small_contract()
        ledger = self._passing_ledger(contract)
        first_item_rows = [row for row in ledger["rows"] if row["itemId"] == "item-0000"]
        first_item_rows[1]["candidateOutputSha256"] = "f" * 64
        candidate_error_field = (
            "outputAErrors"
            if first_item_rows[2]["candidateSide"] == "output_a"
            else "outputBErrors"
        )
        first_item_rows[2]["adjudication"][candidate_error_field] = ["omission"]

        receipt = _EVALUATOR.evaluate_review(ledger, contract)

        self.assertEqual(receipt["status"], "failed")
        self.assertIn(
            "candidate_output_identity_inconsistent_across_comparators",
            receipt["blockers"],
        )
        self.assertIn(
            "candidate_error_labels_inconsistent_across_comparators",
            receipt["blockers"],
        )

    def _small_contract(self) -> dict:
        contract = copy.deepcopy(self.contract)
        for phase in contract["populationMinimums"].values():
            phase["distinctItemsPerDirectionDomainCell"] = 10
        return contract

    @staticmethod
    def _passing_ledger(contract: dict) -> dict:
        comparators = contract["blockingComparators"]
        rows = []
        item_count = 0
        for direction in contract["scope"]["directions"]:
            for domain in contract["scope"]["domains"]:
                for local_index in range(10):
                    item_id = f"item-{item_count:04d}"
                    candidate_side = "output_a" if item_count % 2 == 0 else "output_b"
                    preference = (
                        "output_a_better" if candidate_side == "output_a" else "output_b_better"
                    )
                    for comparator_index, comparator in enumerate(comparators):
                        unit_id = f"{item_id}-comparator-{comparator_index}"
                        reviewer_record = {
                            "preference": preference,
                            "outputAErrors": [],
                            "outputBErrors": [],
                        }
                        rows.append(
                            {
                                "unitId": unit_id,
                                "itemId": item_id,
                                "direction": direction,
                                "domain": domain,
                                "comparatorId": comparator,
                                "candidateSide": candidate_side,
                                "candidateOutputSha256": hashlib.sha256(
                                    f"candidate-{item_id}".encode("utf-8")
                                ).hexdigest(),
                                "comparatorOutputSha256": hashlib.sha256(
                                    f"{comparator}-{item_id}".encode("utf-8")
                                ).hexdigest(),
                                "blindingReceiptSha256": "1" * 64,
                                "mappingReceiptSha256": "2" * 64,
                                "reviewers": [
                                    {
                                        "reviewerId": "reviewer-one",
                                        "qualificationReceiptSha256": "3" * 64,
                                        **reviewer_record,
                                    },
                                    {
                                        "reviewerId": "reviewer-two",
                                        "qualificationReceiptSha256": "4" * 64,
                                        **reviewer_record,
                                    },
                                ],
                                "adjudication": {
                                    "status": "complete",
                                    "adjudicatorId": "adjudicator-one",
                                    "qualificationReceiptSha256": "5" * 64,
                                    **reviewer_record,
                                },
                            }
                        )
                    item_count += 1
        return {
            "schemaVersion": 1,
            "reviewId": "test-review",
            "reviewContractId": contract["reviewContractId"],
            "phase": "checkpoint_selection",
            "population": {
                "populationId": "test-population",
                "populationSha256": "6" * 64,
                "expectedDistinctItems": item_count,
            },
            "candidate": {
                "systemId": "candidate",
                "artifactSha256": "7" * 64,
            },
            "comparators": [
                {"modelId": comparator, "artifactSha256": f"{8 + index:x}" * 64}
                for index, comparator in enumerate(comparators)
            ],
            "rows": rows,
        }


if __name__ == "__main__":
    unittest.main()
