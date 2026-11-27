"""Automated verification suite for BITS paired-switch-v1 (Sections 1-6)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dev_families import DEV_PROBLEMS, get_problem, verify_dev_family_suite
from helpers import HELPER_SPECS, skip_equal, verify_all_helpers
from predictor import predict_switch_benefit, summarize_paired_search_outcomes
from run_experiment import CONTRACT_PATH, run_engine_verification
from switch_engine import (
    ByteLevelTestTokenizer,
    PairedSwitchAdapter,
    build_synthetic_transformer,
    run_forced_call_check,
    verify_cache_reuse_and_rebuild_parity,
)
from switch_point import (
    assert_helper_token_absent,
    build_switch_point,
    verify_switch_point_snapshot,
)
from verifier import HELPER_TOKEN_SYMBOL, SingleBindRegistry, verify_candidate


class Section1SwitchPointTests(unittest.TestCase):
    def test_skip_equal_boundary_behaviors(self):
        # Empty suffix
        self.assertEqual(skip_equal([], 0), 0)
        self.assertEqual(skip_equal([1, 2], 2), 2)
        # Run of duplicates
        self.assertEqual(skip_equal([2, 2, 2, 5], 0), 3)
        self.assertEqual(skip_equal([1, 4, 4, 4, 9], 1), 4)
        # End of array
        self.assertEqual(skip_equal([1, 3, 3], 1), 3)
        self.assertEqual(skip_equal([1, 5], 1), 2)
        with self.assertRaises(ValueError):
            skip_equal([1, 2], -1)

    def test_canonical_switch_point_roundtrip_and_absence_check(self):
        tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
        prob = get_problem("dup_02_unique_triplets_zero")
        snap = build_switch_point(
            problem=prob,
            tokenizer_encode=tok.encode,
            helper_token_id=tok.helper_token_id,
            remaining_attempt_cap=32,
            remaining_token_budget=32 * 384,
            setup_budget_steps=16,
            seed=42,
        )
        check = verify_switch_point_snapshot(snap)
        self.assertTrue(check["absence_ok"])
        self.assertTrue(check["rng_restore_exact"])
        self.assertTrue(check["exposure_matched_exact"])
        self.assertTrue(check["bind_once_enforced"])

    def test_prefix_leak_fails_closed(self):
        with self.assertRaises(AssertionError):
            assert_helper_token_absent(
                [{"role": "tool", "content": "Mentioned <H0> early"}],
                "Mentioned <H0> early",
                [1, 2, 3],
                helper_token_symbol="<H0>",
                helper_token_id=259,
            )
        with self.assertRaises(AssertionError):
            assert_helper_token_absent(
                [{"role": "user", "content": "clean text"}],
                "clean text",
                [1, 259, 3],
                helper_token_symbol="<H0>",
                helper_token_id=259,
            )

    def test_bind_once_rejects_second_binding_and_verifier_keeps_refusals_timeouts(self):
        reg = SingleBindRegistry()
        reg.bind_once("skip_equal", 259)
        with self.assertRaises(RuntimeError):
            reg.bind_once("merge_span", 259)

        refusal = verify_candidate("", "f", [{"label": "a", "args": [1], "expected": 1}])
        self.assertEqual(refusal["status"], "refusal")
        self.assertFalse(refusal["passed"])

        timeout = verify_candidate(
            "def f(x):\n    while True:\n        pass\n",
            "f",
            [{"label": "a", "args": [1], "expected": 1}],
            timeout_seconds=0.2,
        )
        self.assertEqual(timeout["status"], "timeout")
        self.assertFalse(timeout["passed"])


class Section2And3EngineTests(unittest.TestCase):
    def test_tied_and_untied_engines_pass_all_gates(self):
        for tied in (True, False):
            rep = run_engine_verification(
                tie_word_embeddings=tied,
                device="cpu",
                setup_budget_steps=8,
            )
            self.assertTrue(rep["passed"], f"Engine verification failed for tied={tied}: {rep}")
            self.assertEqual(rep["adapter_detected_tied_embeddings"], tied)
            self.assertTrue(rep["equal_spend_ok"])
            self.assertTrue(rep["all_invariance_ok"])
            # Score-only must keep input row bit-exact untouched while updating output row.
            so_inv = rep["arms"]["score_only_alias"]["invariance"]
            self.assertEqual(so_inv["h0_input_row_max_abs_diff"], 0.0)
            self.assertGreater(so_inv["h0_output_row_max_abs_diff"], 0.0)
            # Score-and-input must update both rows independently even when tied=True.
            si_inv = rep["arms"]["score_and_input_alias"]["invariance"]
            self.assertGreater(si_inv["h0_output_row_max_abs_diff"], 0.0)
            self.assertGreater(si_inv["h0_input_row_max_abs_diff"], 0.0)
            # Cache reuse & forced-call isolation gates.
            self.assertEqual(rep["cache_reuse_check"]["historical_kv_max_abs_diff"], 0.0)
            self.assertTrue(rep["cache_reuse_check"]["stale_logits_avoided"])
            self.assertEqual(rep["forced_call_check"]["pre_call_max_abs_diff"], 0.0)
            self.assertTrue(rep["forced_call_check"]["fixture_passed"])
            self.assertTrue(rep["forced_call_check"]["input_effect_isolated"])
            self.assertIsNone(rep["forced_call_check"]["free_search_benefit_established"])

    def test_forced_call_check_detects_pre_call_leak(self):
        """Negative control: if <H0> is present before forced call, fixture rejects it."""
        tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
        model = build_synthetic_transformer(vocab_size=tok.vocab_size, tie_word_embeddings=True, seed=9)
        adapter = PairedSwitchAdapter(model, helper_token_id=tok.helper_token_id)
        try:
            with self.assertRaises(AssertionError):
                run_forced_call_check(
                    adapter,
                    prefix_token_ids=tok.encode("clean prefix"),
                    pre_call_tokens=tok.encode("leaked <H0> before call"),
                    forced_operands_and_body_tokens=tok.encode("(xs, i)"),
                    forced_verifier_response_tokens=tok.encode("fail"),
                    shared_delta_out=torch.ones(64) * 0.1,
                    adapted_delta_in=torch.ones(64) * 0.1,
                )
        finally:
            adapter.close()


class Section4To6DevSuiteAndContractTests(unittest.TestCase):
    def test_all_helpers_and_three_dev_families_verify(self):
        helpers_rep = verify_all_helpers()
        self.assertEqual(set(helpers_rep.keys()), {"skip_equal", "merge_span", "push_unvisited"})

        suite_rep = verify_dev_family_suite(helper_token_id=259)
        self.assertEqual(suite_rep["total_problems"], 9)
        self.assertEqual(
            set(suite_rep["families"]),
            {"duplicate_handling", "interval_processing", "graph_traversal"},
        )
        self.assertEqual(
            set(suite_rep["utility_regimes"]),
            {"useful_once", "repeatedly_useful", "irrelevant_decoy"},
        )

    def test_switch_predictor_separates_useful_helpers_from_decoys_without_oracle_labels(self):
        tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
        for prob in DEV_PROBLEMS:
            for cap in (2, 32):
                snap = build_switch_point(
                    problem=prob,
                    tokenizer_encode=tok.encode,
                    helper_token_id=tok.helper_token_id,
                    remaining_attempt_cap=cap,
                    remaining_token_budget=cap * 384,
                    setup_budget_steps=16,
                )
                # Strip oracle utility_regime before prediction to prove zero label leakage.
                sanitized = dict(snap)
                sanitized["utility_regime"] = "REDACTED"
                pred = predict_switch_benefit(sanitized)
                if prob["utility_regime"] == "irrelevant_decoy":
                    self.assertEqual(
                        pred.decision, "SKIP", f"Decoy {prob['problem_id']} cap={cap} wrongly adapted"
                    )
                else:
                    self.assertEqual(
                        pred.decision, "ADAPT", f"Useful {prob['problem_id']} cap={cap} wrongly skipped"
                    )

    def test_paired_accounting_keeps_refusals_and_timeouts_in_denominator_and_rung4_locked(self):
        synthetic_records = [
            {
                "problem_id": "p1",
                "family": "duplicate_handling",
                "switch_point_id": "p1@cap2",
                "arm": "score_only_alias",
                "solved": True,
                "status": "pass",
                "failed_attempts": 0,
                "helper_calls": 1,
                "total_work_units": 500,
                "work_to_first_verified": 500,
                "elapsed_seconds": 1.0,
                "peak_memory_bytes": 1024,
            },
            {
                "problem_id": "p2",
                "family": "interval_processing",
                "switch_point_id": "p2@cap2",
                "arm": "score_only_alias",
                "solved": False,
                "status": "timeout",
                "failed_attempts": 2,
                "helper_calls": 0,
                "total_work_units": 900,
                "work_to_first_verified": None,
                "elapsed_seconds": 4.0,
                "peak_memory_bytes": 2048,
            },
            {
                "problem_id": "p1",
                "family": "duplicate_handling",
                "switch_point_id": "p1@cap2",
                "arm": "score_and_input_alias",
                "solved": True,
                "status": "pass",
                "failed_attempts": 0,
                "helper_calls": 1,
                "total_work_units": 500,
                "work_to_first_verified": 500,
                "elapsed_seconds": 1.1,
                "peak_memory_bytes": 1024,
            },
            {
                "problem_id": "p2",
                "family": "interval_processing",
                "switch_point_id": "p2@cap2",
                "arm": "score_and_input_alias",
                "solved": False,
                "status": "refusal",
                "failed_attempts": 2,
                "helper_calls": 0,
                "total_work_units": 500,
                "work_to_first_verified": None,
                "elapsed_seconds": 0.5,
                "peak_memory_bytes": 1024,
            },
        ]
        summary = summarize_paired_search_outcomes(synthetic_records, bootstrap_iters=200)
        self.assertEqual(summary["arms"]["score_only_alias"]["total_in_denominator"], 2)
        self.assertEqual(summary["arms"]["score_only_alias"]["timeouts"], 1)
        self.assertEqual(summary["arms"]["score_and_input_alias"]["refusals"], 1)

        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["rung4_gate"]["status"], "LOCKED_PENDING_RUNG3_WIN")
        self.assertTrue(contract["separate_from_existing_papers"])


if __name__ == "__main__":
    unittest.main()
