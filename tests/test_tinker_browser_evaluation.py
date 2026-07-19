"""Tests for the Tinker-to-Doppler browser selection contract."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = ROOT / "projects" / "samer" / "domains" / "tinker_browser" / "evaluate.py"
FIXTURE = ROOT / "projects" / "samer" / "domains" / "tinker_browser" / "fixtures" / "synthetic-pass.json"
SPEC = importlib.util.spec_from_file_location("tinker_browser_evaluate", EVALUATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
EVALUATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = EVALUATOR
SPEC.loader.exec_module(EVALUATOR)


class TinkerBrowserEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_synthetic_fixture_proves_evaluator_mechanics(self) -> None:
        receipt = EVALUATOR.evaluate(self.fixture)
        self.assertEqual(receipt["decision"], "gamma_selected")
        self.assertFalse(receipt["admission"]["promotionAllowed"])
        self.assertTrue(receipt["task"]["passed"])
        self.assertTrue(receipt["retention"]["passed"])
        self.assertFalse(receipt["determinism"]["crossDeviceNumerical"]["passed"])
        self.assertFalse(receipt["determinism"]["crossDeviceNumerical"]["required"])
        self.assertEqual(len(receipt["receiptSha256"]), 64)

    def test_receipt_identity_is_deterministic(self) -> None:
        self.assertEqual(
            EVALUATOR.evaluate(copy.deepcopy(self.fixture))["receiptSha256"],
            EVALUATOR.evaluate(copy.deepcopy(self.fixture))["receiptSha256"],
        )

    def test_doppler_parity_failure_blocks_selection(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["evidence"]["dopplerParity"]["decision"] = "block"
        receipt = EVALUATOR.evaluate(candidate)
        self.assertEqual(receipt["decision"], "blocked")
        self.assertIn("dopplerParity_blocked", receipt["blockers"])

    def test_retention_regression_blocks_selection(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["metrics"]["retention"]["candidate"] = 0.7
        receipt = EVALUATOR.evaluate(candidate)
        self.assertIn("sealed_retention_floor_failed", receipt["blockers"])

    def test_required_cross_device_numerical_failure_blocks(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["determinism"]["crossDeviceNumerical"]["required"] = True
        receipt = EVALUATOR.evaluate(candidate)
        self.assertIn("determinism_crossDeviceNumerical_failed", receipt["blockers"])

    def test_unknown_trainer_fails_closed(self) -> None:
        candidate = copy.deepcopy(self.fixture)
        candidate["artifact"]["trainer"] = "unknown/trainer"
        with self.assertRaisesRegex(EVALUATOR.EvaluationContractError, "thinking-machines/tinker"):
            EVALUATOR.validate_input(candidate)


if __name__ == "__main__":
    unittest.main()
