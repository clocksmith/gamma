"""Automated verification suite for BITS paired-switch-v1 (Sections 1-6)."""

from __future__ import annotations

import io
import json
import sys
import time
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dev_families import DEV_PROBLEMS, get_problem, verify_dev_family_suite
from helpers import HELPER_SPECS, skip_equal, verify_all_helpers
from predictor import predict_switch_benefit, summarize_paired_search_outcomes
from run_experiment import (
    CONTRACT_PATH,
    _collect_eos_token_ids,
    _extract_python_code,
    _run_live_arm,
    cmd_run_live,
    run_engine_verification,
    verify_helper_token_roundtrip,
)
from switch_engine import (
    ByteLevelTestTokenizer,
    HelperAliasTokenizer,
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
from work_budget import ArmBudget


class LiveBudgetTests(unittest.TestCase):
    """Exercise the admission check on the same arm loop that run-live executes."""

    def run_arm(self, *, setup_ns, generation_ns=0, verification_ns=0, verdicts=(True,)):
        now = 0
        window = 50_000_000
        budget = ArmBudget(100_000_000, shared_setup_ns=10_000_000,
                           synchronize=lambda: None, clock=lambda: now)

        def adapt(*_args, **kwargs):
            nonlocal now
            now += setup_ns
            return {"tokens_processed": 11, "delta_in": None, "delta_out": None}

        def generate(*_args, **kwargs):
            nonlocal now
            now += generation_ns
            return [7], 1

        answers = iter(verdicts)

        def verify(*_args, **kwargs):
            nonlocal now
            now += verification_ns
            passed = next(answers)
            return {"passed": passed, "status": "pass" if passed else "fail"}

        snap = {"prefix_token_ids": [1], "rng_state": {},
                "switch_exposure": {"alias_arms": "skip_equal(xs, i)"}}
        with (
            patch("run_experiment.build_switch_adaptation_sequences", return_value=[]),
            patch("run_experiment.adapt_arm_equal_budget", side_effect=adapt),
            patch("run_experiment.restore_rng_state"),
            patch("run_experiment._sample_continuation_from_cache", side_effect=generate) as generator,
            patch("run_experiment.verify_candidate", side_effect=verify) as verifier,
        ):
            record, _ = _run_live_arm(
                "score_and_input_alias", DEV_PROBLEMS[0], snap, Mock(), Mock(helper_token_id=259),
                Mock(decode=Mock(return_value="pass")), budget, attempt_cap=2, setup_steps=1,
                learning_rate=.05, max_new_tokens=8, verifier_timeout=window / 1e9,
            )
        self.assertEqual(record["verifier_calls"], verifier.call_count)
        self.assertAlmostEqual(sum(record["phase_ns"].values()) / 1e9, record["total_work_units"])
        return record, generator, verifier

    def test_setup_leaves_one_nanosecond_short_of_one_verification(self):
        record, generator, verifier = self.run_arm(setup_ns=40_000_001)
        verifier.assert_not_called()
        generator.assert_not_called()
        self.assertFalse(record["solved"])
        self.assertEqual(record["status"], "budget_exhausted")
        self.assertEqual(record["remaining_ns"], 49_999_999)
        self.assertEqual(record["phase_ns"]["shared_setup"], 10_000_000)
        self.assertEqual(record["phase_ns"]["setup"], 40_000_001)

    def test_generation_can_spend_the_verifier_window(self):
        record, generator, verifier = self.run_arm(setup_ns=0, generation_ns=40_000_001)
        generator.assert_called_once()
        verifier.assert_not_called()
        self.assertEqual(record["blocked_phase"], "verification")
        self.assertIsNone(record["work_to_first_verified"])

    def test_verifier_admits_exact_reservation_and_charges_actual_use(self):
        record, _, verifier = self.run_arm(setup_ns=40_000_000, verification_ns=50_000_000)
        verifier.assert_called_once()
        self.assertTrue(record["solved"])
        self.assertEqual(record["remaining_ns"], 0)
        self.assertEqual(record["work_to_first_verified"], .1)
        self.assertEqual(record["phase_ns"]["verification"], 50_000_000)

        retry, _, verifier = self.run_arm(setup_ns=10_000_000, verification_ns=15_000_000,
                                          verdicts=(False, True))
        self.assertEqual(verifier.call_count, 2)
        self.assertEqual(retry["failed_attempts"], 1)
        self.assertEqual(retry["work_to_first_verified"], .05)

    def test_late_verifier_pass_is_rejected_and_overrun_recorded(self):
        record, _, verifier = self.run_arm(setup_ns=40_000_000, verification_ns=50_000_001)
        verifier.assert_called_once()
        self.assertFalse(record["solved"])
        self.assertEqual(record["status"], "budget_exhausted")
        self.assertEqual(record["overrun_ns"], 1)
        self.assertIsNone(record["work_to_first_verified"])

    def test_verifier_process_stops_at_arm_deadline(self):
        result = verify_candidate(
            "def f():\n    import time\n    time.sleep(5)\n    return 1",
            "f", [{"args": [], "expected": 1}], timeout_seconds=10,
            deadline_ns=time.perf_counter_ns() + 100_000_000,
        )
        self.assertEqual(result["status"], "timeout")
        self.assertLess(result["elapsed_seconds"], 3)

    def test_live_entry_records_all_arms_on_exhausted_and_admitted_budgets(self):
        # Use in-memory untrained weights and two one-token attempts, entirely on CPU.
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        tok = ByteLevelTestTokenizer(helper_token_id=259)
        tokenizer = Mock(
            get_vocab=lambda: {HELPER_TOKEN_SYMBOL: 259},
            convert_tokens_to_ids=lambda _: 259, eos_token_id=tok.eos_token_id,
            encode=lambda text, **_: tok.encode(text), decode=lambda ids, **_: tok.decode(ids),
        )
        model = build_synthetic_transformer(hidden_size=16, num_hidden_layers=1, num_attention_heads=2)
        contract = json.loads(CONTRACT_PATH.read_text())
        contract["search_budgets"]["max_new_tokens_per_attempt"] = 1
        with TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(contract))
            output = Path(directory) / "receipt.json"
            for limit in (1e-9, 30):
                with (
                    self.subTest(seconds=limit),
                    patch("run_experiment.CONTRACT_PATH", contract_path),
                    patch("transformers.AutoTokenizer.from_pretrained", return_value=tokenizer),
                    patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=model),
                    patch("run_experiment.DEV_PROBLEMS", [DEV_PROBLEMS[0]]),
                    patch("run_experiment.verify_candidate", wraps=verify_candidate) as verifier,
                    redirect_stdout(io.StringIO()),
                ):
                    args = Namespace(model="in-memory-fixture", allow_download=False, split="dev",
                                     dtype="float32", device="cpu", reserved_token_id=None,
                                     attempt_caps="2", setup_steps=1, arm_budget_seconds=limit,
                                     output=str(output))
                    self.assertEqual(cmd_run_live(args), 0)
                    receipt = json.loads(output.read_text())
                    rows = receipt["records"]
                    self.assertEqual(len(rows), 4)
                    self.assertEqual(len({r["phase_ns"]["shared_setup"] for r in rows}), 1)
                    self.assertTrue(all(r["budget_limit_ns"] == round(limit * 1e9) for r in rows))
                    self.assertEqual(verifier.call_count, sum(r["verifier_calls"] for r in rows))
                    if limit == 30:
                        self.assertEqual(verifier.call_count, 8)
                        for row in rows:
                            self.assertGreater(row["phase_ns"]["setup"], 0)
                            self.assertGreater(row["phase_ns"]["generation"], 0)
                            self.assertGreater(row["phase_ns"]["verification"], 0)
                            self.assertGreater(row["remaining_ns"], 0)
                        self.assertTrue(receipt["gate_receipts"][0]["forced_call"]["fixture_passed"])
                    else:
                        verifier.assert_not_called()
                        for arm in receipt["summary"]["arms"].values():
                            self.assertEqual(arm["total_in_denominator"], 1)
                            self.assertEqual(arm["budget_exhaustions"], 1)

    def test_live_runner_with_tokenizer_lacking_literal_h0_and_reserved_token_id(self):
        """Regression test: tokenizer lacking literal `<H0>` with `--reserved-token-id`.

        Verifies:
        1. `<H0>` encodes to exactly one token ID (`[reserved_id]`), not subwords.
        2. Emitting `[reserved_id]` decodes to `<H0>` (not native `<unused0>`) and
           lowers to an executable helper call in `verify_candidate`.
        3. `cmd_run_live` completes all 4 arms without raising an exception and
           adapts `score_only_alias` and `score_and_input_alias` cleanly.
        """
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        reserved_id = 259

        class NoLiteralH0Tokenizer:
            """Tokenizer whose vocab has `<unused0>` at ID 259 and NO literal `<H0>`."""

            eos_token_id = 258
            bos_token_id = 257

            def get_vocab(self):
                vocab = {f"byte_{i}": i for i in range(256)}
                vocab["<bos>"] = 257
                vocab["<eos>"] = 258
                vocab["<unused0>"] = reserved_id
                return vocab

            def encode(self, text, add_special_tokens=False):
                # Deliberately splits literal "<H0>" into 4 raw UTF-8 bytes!
                return list(text.encode("utf-8"))

            def decode(self, ids, skip_special_tokens=False):
                out = []
                buf = bytearray()
                for tid in ids:
                    if tid == reserved_id:
                        if buf:
                            out.append(buf.decode("utf-8", errors="replace"))
                            buf.clear()
                        if not skip_special_tokens:
                            out.append("<unused0>")
                    elif tid == self.eos_token_id:
                        if buf:
                            out.append(buf.decode("utf-8", errors="replace"))
                            buf.clear()
                        if not skip_special_tokens:
                            out.append("<eos>")
                    elif 0 <= tid < 256:
                        buf.append(tid)
                if buf:
                    out.append(buf.decode("utf-8", errors="replace"))
                return "".join(out)

        raw_tok = NoLiteralH0Tokenizer()
        # Confirm raw tokenizer reproduces the failure condition.
        self.assertNotIn(HELPER_TOKEN_SYMBOL, raw_tok.get_vocab())
        self.assertEqual(len(raw_tok.encode(HELPER_TOKEN_SYMBOL)), 4)
        self.assertEqual(raw_tok.decode([reserved_id], skip_special_tokens=False), "<unused0>")

        alias_tok = HelperAliasTokenizer(
            raw_tok, helper_token_id=reserved_id, helper_symbol=HELPER_TOKEN_SYMBOL, vocab_size=264
        )
        self.assertEqual(alias_tok.encode(HELPER_TOKEN_SYMBOL), [reserved_id])
        self.assertEqual(alias_tok.decode([reserved_id], skip_special_tokens=True), HELPER_TOKEN_SYMBOL)
        self.assertEqual(alias_tok.decode([reserved_id], skip_special_tokens=False), HELPER_TOKEN_SYMBOL)

        # Verify generated IDs containing reserved_id + trailing EOS decode to executable call.
        sample_code = (
            "def count_unique_sorted(xs):\n"
            "    i = 0\n"
            "    out = 0\n"
            "    while i < len(xs):\n"
            "        i = <H0>(xs, i)\n"
            "        out += 1\n"
            "    return out\n"
        )
        encoded = alias_tok.encode(sample_code) + [raw_tok.eos_token_id]
        self.assertEqual(encoded.count(reserved_id), 1)
        decoded = alias_tok.decode(encoded, skip_special_tokens=True)
        self.assertIn("<H0>(xs, i)", decoded)
        self.assertNotIn("<eos>", decoded)
        binding = SingleBindRegistry().bind_once("skip_equal", reserved_id)
        verdict = verify_candidate(
            decoded,
            entry_point="count_unique_sorted",
            cases=[{"label": "dups", "args": [[1, 1, 2, 2, 2, 5]], "expected": 3}],
            helper_name="skip_equal",
            binding=binding,
            arm_uses_alias=True,
        )
        self.assertTrue(verdict["passed"], verdict)
        self.assertEqual(verdict["runtime_helper_calls"], 3)

        rt = verify_helper_token_roundtrip(alias_tok)
        self.assertTrue(rt["probe_executable_passed"])
        self.assertEqual(rt["encoded_symbol_ids"], [reserved_id])

        # Collision and bounds checks fail closed.
        with self.assertRaises(ValueError):
            HelperAliasTokenizer(raw_tok, helper_token_id=raw_tok.eos_token_id, vocab_size=264)
        with self.assertRaises(ValueError):
            HelperAliasTokenizer(raw_tok, helper_token_id=300, vocab_size=264)

        # Full cmd_run_live end-to-end with `--reserved-token-id 259` and no literal `<H0>`.
        model = build_synthetic_transformer(
            vocab_size=264, hidden_size=16, num_hidden_layers=1, num_attention_heads=2
        )
        contract = json.loads(CONTRACT_PATH.read_text())
        contract["search_budgets"]["max_new_tokens_per_attempt"] = 2
        with TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(contract))
            output = Path(directory) / "receipt.json"
            with (
                patch("run_experiment.CONTRACT_PATH", contract_path),
                patch("transformers.AutoTokenizer.from_pretrained", return_value=raw_tok),
                patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=model),
                patch("run_experiment.DEV_PROBLEMS", [DEV_PROBLEMS[0]]),
                redirect_stdout(io.StringIO()),
            ):
                args = Namespace(
                    model="in-memory-no-h0",
                    allow_download=False,
                    split="dev",
                    dtype="float32",
                    device="cpu",
                    reserved_token_id=reserved_id,
                    attempt_caps="2",
                    setup_steps=2,
                    arm_budget_seconds=30.0,
                    output=str(output),
                )
                self.assertEqual(cmd_run_live(args), 0)
                receipt = json.loads(output.read_text())
                self.assertEqual(len(receipt["records"]), 4)
                self.assertTrue(receipt["helper_token_roundtrip"]["probe_executable_passed"])
                self.assertTrue(receipt["gate_receipts"][0]["forced_call"]["fixture_passed"])
                self.assertTrue(receipt["gate_receipts"][0]["forced_call"]["input_effect_isolated"])

    def test_extract_python_code_handles_prompt_opened_fence_and_multi_eos(self):
        # When prompt suffix opened ```python\n, extract first block before closing ```.
        raw = "def f(xs):\n    return xs\n```\nextra text\n```python\ndef wrong():\n    pass\n```"
        self.assertEqual(_extract_python_code(raw, prompt_opened_fence=True), "def f(xs):\n    return xs\n")
        self.assertEqual(_extract_python_code("def g():\n    return 1\n```", prompt_opened_fence=True), "def g():\n    return 1\n")
        tok = Mock(eos_token_id=151645)
        model = Mock(generation_config=Mock(eos_token_id=[151645, 151643]))
        self.assertEqual(_collect_eos_token_ids(tok, model, exclude_id=151665), {151645, 151643})


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
