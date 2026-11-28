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

from dev_families import ALL_DEV_PROBLEMS, DEV_PROBLEMS, DEV_VAL_PROBLEMS, get_problem, verify_dev_family_suite
from helpers import HELPER_SPECS, skip_equal, verify_all_helpers
from predictor import (
    evaluate_rung2_predictor,
    evaluate_rung3_dev_gate,
    evaluate_stage1_helper_qualification,
    is_full_run_gpu_reservation_verified,
    predict_switch_benefit,
    summarize_paired_search_outcomes,
)
from run_experiment import (
    CONTRACT_PATH,
    ExclusiveGpuLease,
    _collect_eos_token_ids,
    _extract_python_code,
    _run_live_arm,
    build_stage2_paired_installation_items,
    check_exclusive_gpu,
    cmd_eval_rung2,
    cmd_run_live,
    cmd_run_stage2_val,
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
            verdict = next(answers)
            if isinstance(verdict, dict):
                return verdict
            return {"passed": verdict, "status": "pass" if verdict else "fail"}

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
        record, _, verifier = self.run_arm(
            setup_ns=40_000_000,
            verification_ns=50_000_001,
            verdicts=({"passed": True, "status": "pass", "syntactic_helper_calls": 2, "runtime_helper_calls": 5},),
        )
        verifier.assert_called_once()
        self.assertFalse(record["solved"])
        self.assertEqual(record["status"], "budget_exhausted")
        self.assertEqual(record["overrun_ns"], 1)
        self.assertIsNone(record["work_to_first_verified"])
        self.assertEqual(record["syntactic_helper_calls_all_attempts"], 2)
        self.assertEqual(record["runtime_helper_calls_all_attempts"], 5)
        self.assertEqual(record["passing_syntactic_helper_calls"], 0)
        self.assertEqual(record["passing_runtime_helper_calls"], 0)
        self.assertFalse(record["solved_with_executed_helper"])

    def test_executed_helper_calls_on_passing_candidates_separated_from_mentions(self):
        # Attempt 1 fails with 3 syntactic mentions and 2 runtime calls; attempt 2 passes with 1 mention and 4 runtime calls.
        record, _, _ = self.run_arm(
            setup_ns=10_000_000,
            verification_ns=15_000_000,
            verdicts=(
                {"passed": False, "status": "fail", "syntactic_helper_calls": 3, "runtime_helper_calls": 2},
                {"passed": True, "status": "pass", "syntactic_helper_calls": 1, "runtime_helper_calls": 4},
            ),
        )
        self.assertTrue(record["solved"])
        self.assertEqual(record["syntactic_helper_calls_all_attempts"], 4)
        self.assertEqual(record["runtime_helper_calls_all_attempts"], 6)
        self.assertEqual(record["passing_syntactic_helper_calls"], 1)
        self.assertEqual(record["passing_runtime_helper_calls"], 4)
        self.assertTrue(record["solved_with_executed_helper"])

        # Passing attempt with zero executed helper calls keeps mentions separate from passing execution.
        no_helper_pass, _, _ = self.run_arm(
            setup_ns=10_000_000,
            verification_ns=15_000_000,
            verdicts=(
                {"passed": False, "status": "fail", "syntactic_helper_calls": 5, "runtime_helper_calls": 0},
                {"passed": True, "status": "pass", "syntactic_helper_calls": 0, "runtime_helper_calls": 0},
            ),
        )
        self.assertTrue(no_helper_pass["solved"])
        self.assertEqual(no_helper_pass["syntactic_helper_calls_all_attempts"], 5)
        self.assertEqual(no_helper_pass["passing_runtime_helper_calls"], 0)
        self.assertFalse(no_helper_pass["solved_with_executed_helper"])
        summary = summarize_paired_search_outcomes([record, no_helper_pass], bootstrap_iters=50)
        arm = summary["arms"]["score_and_input_alias"]
        self.assertEqual(arm["solved"], 2)
        self.assertEqual(arm["solved_with_executed_helper"], 1)
        self.assertEqual(arm["solved_without_executed_helper"], 1)
        self.assertEqual(arm["total_syntactic_helper_calls_all_attempts"], 9)
        self.assertEqual(arm["passing_runtime_helper_calls"], 4)

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
        prob = get_problem("rle_02_stream_diff_metrics")
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
            reg.bind_once("apply_weighted_span", 259)

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

        noisy_pass = verify_candidate(
            "print('top-level example output')\ndef f(x):\n    print('inside', x)\n    return x + 1\n",
            "f",
            [{"label": "a", "args": [2], "expected": 3}],
        )
        self.assertTrue(noisy_pass["passed"], noisy_pass)
        self.assertEqual(noisy_pass["status"], "pass")

        exiting = verify_candidate(
            "import sys\nsys.exit(0)\ndef f(x):\n    return x\n",
            "f",
            [{"label": "a", "args": [1], "expected": 1}],
        )
        self.assertFalse(exiting["passed"])
        self.assertEqual(exiting["status"], "syntax_or_load_error")


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
            # Score-only and score-and-input must optimize the exact same loss positions and step-0 loss.
            so_rep = rep["arms"]["score_only_alias"]
            si_rep = rep["arms"]["score_and_input_alias"]
            self.assertTrue(so_rep["loss_positions_matched"])
            self.assertTrue(si_rep["loss_positions_matched"])
            self.assertEqual(so_rep["loss_position_counts"], si_rep["loss_position_counts"])
            self.assertGreater(so_rep["loss_position_counts"]["selection"], 0)
            self.assertGreater(so_rep["loss_position_counts"]["post_call"], 0)
            self.assertAlmostEqual(so_rep["initial_loss"], si_rep["initial_loss"], places=6)
            # Score-only must keep input row bit-exact untouched while updating output row.
            so_inv = so_rep["invariance"]
            self.assertEqual(so_inv["h0_input_row_max_abs_diff"], 0.0)
            self.assertGreater(so_inv["h0_output_row_max_abs_diff"], 0.0)
            # Score-and-input must update both rows independently even when tied=True.
            si_inv = si_rep["invariance"]
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
    def test_all_six_helpers_and_both_dev_family_splits_verify(self):
        helpers_rep = verify_all_helpers()
        self.assertEqual(
            set(helpers_rep.keys()),
            {
                "skip_equal",
                "advance_rle_block",
                "apply_weighted_span",
                "step_frame_parser",
                "parse_semver_key",
                "shift_business_day",
                "eval_safe_op",
            },
        )

        suite_rep = verify_dev_family_suite(helper_token_id=259, problems=ALL_DEV_PROBLEMS)
        self.assertEqual(suite_rep["total_problems"], 24)
        self.assertEqual(
            set(suite_rep["families"]),
            {
                "run_codec",
                "interval_algebra",
                "protocol_fsm",
                "version_semver",
                "calendar_business",
                "expr_rpn_vm",
            },
        )
        self.assertEqual(
            set(suite_rep["utility_regimes"]),
            {"useful_once", "repeatedly_useful", "irrelevant_decoy"},
        )
        # Ensure train-dev and validation-dev family sets are strictly disjoint.
        train_fams = {p["family"] for p in DEV_PROBLEMS}
        val_fams = {p["family"] for p in DEV_VAL_PROBLEMS}
        self.assertEqual(train_fams & val_fams, set())

    def test_frozen_helper_agnostic_predictor_works_on_train_and_separate_val_dev_families(self):
        tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
        for prob in ALL_DEV_PROBLEMS:
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
                        pred.decision,
                        "SKIP",
                        f"Decoy {prob['problem_id']} cap={cap} wrongly adapted ({pred.visible_features})",
                    )
                    self.assertLess(pred.predicted_net_benefit, 0.25)
                else:
                    self.assertEqual(
                        pred.decision,
                        "ADAPT",
                        f"Useful {prob['problem_id']} cap={cap} wrongly skipped ({pred.visible_features})",
                    )

    def test_stage1_helper_qualification_requires_executed_helper_wins_across_families(self):
        # Case 1: ordinary beats no_helper with executed helper solves in >= 2 families -> qualified.
        good_recs = [
            # duplicate_handling (useful_once): ordinary solves using helper, no_helper fails
            {"problem_id": "d1", "family": "duplicate_handling", "utility_regime": "useful_once",
             "switch_point_id": "d1@cap32", "arm": "no_helper", "solved": False, "status": "fail",
             "passing_runtime_helper_calls": 0, "total_work_units": 30.0},
            {"problem_id": "d1", "family": "duplicate_handling", "utility_regime": "useful_once",
             "switch_point_id": "d1@cap32", "arm": "ordinary_named_fn", "solved": True, "status": "pass",
             "passing_runtime_helper_calls": 3, "total_work_units": 12.0, "work_to_first_verified": 12.0},
            # interval_processing (repeatedly_useful): ordinary solves using helper, no_helper fails
            {"problem_id": "i1", "family": "interval_processing", "utility_regime": "repeatedly_useful",
             "switch_point_id": "i1@cap32", "arm": "no_helper", "solved": False, "status": "fail",
             "passing_runtime_helper_calls": 0, "total_work_units": 30.0},
            {"problem_id": "i1", "family": "interval_processing", "utility_regime": "repeatedly_useful",
             "switch_point_id": "i1@cap32", "arm": "ordinary_named_fn", "solved": True, "status": "pass",
             "passing_runtime_helper_calls": 5, "total_work_units": 15.0, "work_to_first_verified": 15.0},
            # graph_traversal (irrelevant_decoy): tie
            {"problem_id": "g3", "family": "graph_traversal", "utility_regime": "irrelevant_decoy",
             "switch_point_id": "g3@cap32", "arm": "no_helper", "solved": True, "status": "pass",
             "passing_runtime_helper_calls": 0, "total_work_units": 10.0, "work_to_first_verified": 10.0},
            {"problem_id": "g3", "family": "graph_traversal", "utility_regime": "irrelevant_decoy",
             "switch_point_id": "g3@cap32", "arm": "ordinary_named_fn", "solved": True, "status": "pass",
             "passing_runtime_helper_calls": 0, "total_work_units": 11.0, "work_to_first_verified": 11.0},
        ]
        res_ok = evaluate_stage1_helper_qualification(good_recs, bootstrap_iters=100)
        self.assertTrue(res_ok["qualified"], res_ok)
        self.assertEqual(res_ok["verdict"], "HELPER_QUALIFIED_FOR_STAGE2")

        # Case 2: ordinary solves WITHOUT executing the helper (passing_runtime_helper_calls == 0) -> fails closed.
        no_exec_recs = [dict(r, passing_runtime_helper_calls=0) for r in good_recs]
        res_bad = evaluate_stage1_helper_qualification(no_exec_recs, bootstrap_iters=100)
        self.assertFalse(res_bad["qualified"])
        self.assertIn("fixture cannot test the alias", res_bad["verdict"])

    def test_stage2_rung2_predictor_beats_all_three_baselines_and_predicts_losses_on_separate_val_families(self):
        tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
        val_items = []
        for prob in DEV_VAL_PROBLEMS:
            for cap in (2, 32):
                snap = build_switch_point(
                    problem=prob,
                    tokenizer_encode=tok.encode,
                    helper_token_id=tok.helper_token_id,
                    remaining_attempt_cap=cap,
                    remaining_token_budget=cap * 384,
                    setup_budget_steps=16,
                )
                # Realized net outcomes: wins on useful problems, losses on decoys.
                if prob["utility_regime"] == "irrelevant_decoy":
                    realized_net = -0.35
                elif prob["utility_regime"] == "repeatedly_useful":
                    realized_net = 0.85 if cap == 32 else 0.45
                else:
                    realized_net = 0.55 if cap == 32 else 0.20
                val_items.append({"snapshot": snap, "realized_net_benefit": realized_net})

        res = evaluate_rung2_predictor(val_items, helper_length_threshold_lines=28)
        self.assertTrue(res["rung2_earned"], res)
        self.assertTrue(res["beats_always_install"])
        self.assertTrue(res["beats_never_install"])
        self.assertTrue(res["beats_simple_helper_length"])
        self.assertTrue(res["predicts_both_wins_and_losses"])
        self.assertGreaterEqual(res["policies"]["frozen_transcript_predictor"]["loss_recall"], 0.85)
        self.assertGreaterEqual(res["policies"]["frozen_transcript_predictor"]["win_recall"], 0.85)

    def test_stage2_eval_rung2_requires_paired_installation_outcomes_and_rejects_stage1(self):
        """Stage 2 must score the frozen predictor on paired installation outcomes (val split), not Stage 1."""
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        full_gpu_lease = {
            "exclusive_verified": True,
            "lease_held_for_full_run": True,
            "exclusive_maintained_throughout_run": True,
            "watchdog_polls": 4,
            "mid_run_intrusions": [],
        }

        # Build synthetic paired validation outcomes across all 9 DEV_VAL_PROBLEMS (3 disjoint val families).
        paired_records = []
        for prob in DEV_VAL_PROBLEMS:
            for cap in (2, 32):
                useful = prob["utility_regime"] != "irrelevant_decoy"
                inst_solved = bool(useful)
                base_solved = False
                inst_elapsed = 12.0 if useful else 30.0
                base_elapsed = 28.0 if useful else 20.0
                for arm, solved, elapsed, prun in (
                    ("score_only_alias", base_solved, base_elapsed, 0),
                    ("score_and_input_alias", inst_solved, inst_elapsed, 2 if inst_solved else 0),
                ):
                    paired_records.append(
                        {
                            "problem_id": prob["problem_id"],
                            "family": prob["family"],
                            "helper_name": prob["helper_name"],
                            "utility_regime": prob["utility_regime"],
                            "switch_point_id": f"{prob['problem_id']}@cap{cap}",
                            "attempt_cap": cap,
                            "arm": arm,
                            "solved": solved,
                            "status": "pass" if solved else "fail",
                            "elapsed_seconds": elapsed,
                            "total_work_units": elapsed,
                            "budget_limit_ns": 30_000_000_000,
                            "setup_tokens": 512,
                            "setup_loss_position_counts": {"selection": 16, "post_call": 64},
                            "passing_runtime_helper_calls": prun,
                        }
                    )

        raw_valid = {"exclusive_gpu_check": full_gpu_lease, "records": paired_records}

        # 1. Stage 1 comparison (ordinary_named_fn vs no_helper) MUST fail closed.
        with self.assertRaises(SystemExit):
            build_stage2_paired_installation_items(
                raw_valid,
                contract=contract,
                dev_split="val",
                install_arm="ordinary_named_fn",
                baseline_arm="no_helper",
            )
        # 2. Train split MUST fail closed.
        with self.assertRaises(SystemExit):
            build_stage2_paired_installation_items(
                raw_valid,
                contract=contract,
                dev_split="train",
                install_arm="score_and_input_alias",
                baseline_arm="score_only_alias",
            )
        # 3. Unequal total budget between paired arms MUST fail closed.
        bad_budget = json.loads(json.dumps(raw_valid))
        bad_budget["records"][0]["budget_limit_ns"] = 15_000_000_000
        with self.assertRaises(SystemExit):
            build_stage2_paired_installation_items(bad_budget, contract=contract)
        # 4. Unmatched adaptation loss positions MUST fail closed.
        bad_adapt = json.loads(json.dumps(raw_valid))
        bad_adapt["records"][0]["setup_loss_position_counts"] = {"selection": 16, "post_call": 0}
        with self.assertRaises(SystemExit):
            build_stage2_paired_installation_items(bad_adapt, contract=contract)

        # 5. Valid paired validation outcomes pass cmd_eval_rung2 with verified metadata.
        with TemporaryDirectory() as directory:
            outcomes_path = Path(directory) / "stage2_val_outcomes.json"
            receipt_path = Path(directory) / "stage2_receipt.json"
            outcomes_path.write_text(json.dumps(raw_valid), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                rc = cmd_eval_rung2(
                    Namespace(
                        outcomes_json=str(outcomes_path),
                        dev_split="val",
                        install_arm="score_and_input_alias",
                        baseline_arm="score_only_alias",
                        output=str(receipt_path),
                    )
                )
            self.assertEqual(rc, 0)
            s2 = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertTrue(s2["rung2_earned"], s2)
            self.assertTrue(s2["same_helper_paired_installation_verified"])
            self.assertTrue(s2["matched_budget_and_adaptation_verified"])
            self.assertTrue(s2["validation_families_disjoint_from_train"])
            self.assertTrue(s2["outcomes_gpu_reserved_for_full_run"])
            self.assertEqual(s2["install_arm"], "score_and_input_alias")
            self.assertEqual(s2["baseline_arm"], "score_only_alias")
            self.assertEqual(s2["paired_validation_units"], len(DEV_VAL_PROBLEMS) * 2)

    def test_run_stage2_val_executes_paired_adapted_arms_on_val_split(self):
        """Smoke test: `run-stage2-val` runs paired adapted arms on DEV_VAL_PROBLEMS with matched setup."""
        self.addCleanup(torch.set_num_threads, torch.get_num_threads())
        torch.set_num_threads(1)
        tok = ByteLevelTestTokenizer(helper_token_id=259)
        tokenizer = Mock(
            get_vocab=lambda: {HELPER_TOKEN_SYMBOL: 259},
            convert_tokens_to_ids=lambda _: 259,
            eos_token_id=tok.eos_token_id,
            encode=lambda text, **_: tok.encode(text),
            decode=lambda ids, **_: tok.decode(ids),
        )
        model = build_synthetic_transformer(hidden_size=16, num_hidden_layers=1, num_attention_heads=2)
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        contract["search_budgets"]["max_new_tokens_per_attempt"] = 1
        with TemporaryDirectory() as directory:
            contract_path = Path(directory) / "contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            output = Path(directory) / "stage2_val.json"
            with (
                patch("run_experiment.CONTRACT_PATH", contract_path),
                patch("transformers.AutoTokenizer.from_pretrained", return_value=tokenizer),
                patch("transformers.AutoModelForCausalLM.from_pretrained", return_value=model),
                patch("run_experiment.DEV_VAL_PROBLEMS", [DEV_VAL_PROBLEMS[0]]),
                redirect_stdout(io.StringIO()),
            ):
                args = Namespace(
                    model="in-memory-stage2-val",
                    allow_download=False,
                    dtype="float32",
                    device="cpu",
                    reserved_token_id=None,
                    attempt_caps="2",
                    setup_steps=2,
                    arm_budget_seconds=30.0,
                    include_ordinary=False,
                    stage1_receipt=None,
                    require_exclusive_gpu=False,
                    output=str(output),
                )
                self.assertEqual(cmd_run_stage2_val(args), 0)
                receipt = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(receipt["dev_split"], "val")
                self.assertEqual(
                    receipt["paired_installation_arms"],
                    ["score_only_alias", "score_and_input_alias"],
                )
                self.assertEqual(len(receipt["records"]), 2)
                r0, r1 = receipt["records"]
                self.assertEqual(r0["helper_name"], r1["helper_name"])
                self.assertEqual(r0["budget_limit_ns"], r1["budget_limit_ns"])
                self.assertEqual(r0["setup_tokens"], r1["setup_tokens"])
                self.assertEqual(r0["setup_loss_position_counts"], r1["setup_loss_position_counts"])
                self.assertTrue(receipt["gate_receipts"][0]["forced_call"]["fixture_passed"])

    def test_stage3_dev_gate_enforces_prerequisites_controls_and_keeps_holdout_sealed(self):
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        # Build synthetic dev receipt where joint beats BOTH score_only and ordinary across 3 families.
        recs = []
        gates = []
        for fam, pid in [
            ("duplicate_handling", "dup_01"),
            ("interval_processing", "int_01"),
            ("graph_traversal", "graph_01"),
        ]:
            gates.append({"problem_id": pid, "forced_call": {"fixture_passed": True}})
            for arm, solved, prun in [
                ("score_only_alias", False, 0),
                ("ordinary_named_fn", False, 0),
                ("score_and_input_alias", True, 2),
            ]:
                recs.append({
                    "problem_id": pid, "family": fam, "switch_point_id": f"{pid}@cap32",
                    "arm": arm, "solved": solved, "status": "pass" if solved else "fail",
                    "passing_runtime_helper_calls": prun, "total_work_units": 15.0,
                    "work_to_first_verified": 15.0 if solved else None,
                })
        full_gpu_lease = {
            "exclusive_verified": True,
            "lease_held_for_full_run": True,
            "exclusive_maintained_throughout_run": True,
            "watchdog_polls": 6,
            "mid_run_intrusions": [],
        }
        valid_s1 = {"qualified": True, "exclusive_gpu_check": full_gpu_lease}
        valid_s2 = {
            "rung2_earned": True,
            "same_helper_paired_installation_verified": True,
            "matched_budget_and_adaptation_verified": True,
            "validation_families_disjoint_from_train": True,
            "install_arm": "score_and_input_alias",
            "baseline_arm": "score_only_alias",
            "outcomes_gpu_reserved_for_full_run": True,
            "outcomes_exclusive_gpu_check": full_gpu_lease,
        }
        s3_receipt = {
            "exclusive_gpu_check": full_gpu_lease,
            "gate_receipts": gates,
            "records": recs,
        }
        # 1. Missing Stage 1 -> STOP_ON_DEV.
        blocked_s1 = evaluate_rung3_dev_gate(
            s3_receipt, contract=contract,
            stage1_receipt={"qualified": False, "exclusive_gpu_check": full_gpu_lease},
            stage2_receipt=valid_s2,
        )
        self.assertFalse(blocked_s1["dev_gate_passed"])
        self.assertEqual(blocked_s1["verdict"], "STOP_ON_DEV")

        # 2. Point-in-time GPU check only (no whole-run lease / watchdog) -> STOP_ON_DEV.
        point_in_time_s3 = dict(s3_receipt, exclusive_gpu_check={"exclusive_verified": True})
        blocked_pit = evaluate_rung3_dev_gate(
            point_in_time_s3, contract=contract, stage1_receipt=valid_s1, stage2_receipt=valid_s2
        )
        self.assertFalse(blocked_pit["dev_gate_passed"])
        self.assertFalse(blocked_pit["prerequisites"]["stage3_exclusive_gpu_lease_verified"])

        # 3. Mid-run GPU intrusion recorded -> STOP_ON_DEV.
        intruded_gpu = dict(
            full_gpu_lease,
            exclusive_maintained_throughout_run=False,
            exclusive_verified=False,
            mid_run_intrusions=[{"foreign_pids": [777777]}],
        )
        blocked_intrusion = evaluate_rung3_dev_gate(
            dict(s3_receipt, exclusive_gpu_check=intruded_gpu),
            contract=contract, stage1_receipt=valid_s1, stage2_receipt=valid_s2,
        )
        self.assertFalse(blocked_intrusion["dev_gate_passed"])

        # 4. Stage 2 receipt built from Stage 1 (no paired installation) -> STOP_ON_DEV.
        unpaired_s2 = dict(valid_s2, same_helper_paired_installation_verified=False, baseline_arm="no_helper")
        blocked_s2 = evaluate_rung3_dev_gate(
            s3_receipt, contract=contract, stage1_receipt=valid_s1, stage2_receipt=unpaired_s2
        )
        self.assertFalse(blocked_s2["dev_gate_passed"])
        self.assertFalse(blocked_s2["prerequisites"]["stage2_paired_installation_verified"])

        # 5. All prerequisites + whole-run GPU leases + both controls beaten -> ELIGIBLE_FOR_SEALED_DECISION_ONLY.
        passed = evaluate_rung3_dev_gate(
            s3_receipt, contract=contract, stage1_receipt=valid_s1, stage2_receipt=valid_s2
        )
        self.assertTrue(passed["dev_gate_passed"], passed)
        self.assertEqual(passed["verdict"], "ELIGIBLE_FOR_SEALED_DECISION_ONLY")
        self.assertFalse(passed["rung3_claimed"])
        self.assertEqual(passed["holdout_status"], "SEALED")
        self.assertEqual(passed["rung4_status"], "LOCKED_PENDING_RUNG3_WIN")

    def test_exclusive_gpu_lease_holds_flock_and_catches_mid_run_intrusion(self):
        """Whole-run ExclusiveGpuLease locks out concurrent runs and catches transient mid-run PIDs."""
        clean_rocm = Mock(stdout="PID\tPROCESS\n", returncode=0)
        dirty_rocm = Mock(stdout="PID\tPROCESS\n888888\tcompeting_train\n", returncode=0)
        err_rocm = Mock(stdout="", returncode=1)

        with TemporaryDirectory() as directory:
            lock_path = Path(directory) / "gpu0.lock"

            # 1. Clean full-run lease: holds flock (blocking concurrent lease), polls watchdog, releases cleanly.
            with (
                patch("run_experiment.shutil.which", side_effect=lambda cmd: "/usr/bin/rocm-smi" if cmd == "rocm-smi" else None),
                patch("run_experiment.subprocess.run", return_value=clean_rocm),
            ):
                lease1 = ExclusiveGpuLease(
                    "cuda",
                    require_exclusive=True,
                    lock_path=lock_path,
                    poll_interval_seconds=0.02,
                    external_lease_id="bus-lease-test-01",
                    stage="stage3_test",
                )
                with lease1:
                    meta = json.loads(lock_path.read_text(encoding="utf-8"))
                    self.assertEqual(meta["external_lease_id"], "bus-lease-test-01")
                    self.assertEqual(meta["stage"], "stage3_test")
                    # Second concurrent lease on the same lockfile MUST fail closed!
                    with self.assertRaises(RuntimeError):
                        with ExclusiveGpuLease(
                            "cuda",
                            require_exclusive=True,
                            lock_path=lock_path,
                            poll_interval_seconds=0.02,
                            stage="competing",
                        ):
                            pass
                    time.sleep(0.05)

                self.assertTrue(lease1.report["lease_held_for_full_run"])
                self.assertTrue(lease1.report["exclusive_maintained_throughout_run"])
                self.assertGreaterEqual(lease1.report["watchdog_polls"], 1)
                self.assertEqual(lease1.report["mid_run_intrusions"], [])
                self.assertEqual(lease1.report["external_lease_id"], "bus-lease-test-01")
                self.assertTrue(is_full_run_gpu_reservation_verified(lease1.report))
                lease1.raise_if_intruded()

                # After exit, lock is released so a subsequent lease succeeds.
                lease2 = ExclusiveGpuLease(
                    "cuda", require_exclusive=True, lock_path=lock_path, poll_interval_seconds=0.02
                )
                with lease2:
                    pass
                self.assertTrue(is_full_run_gpu_reservation_verified(lease2.report))

            # 2. Transient mid-run intrusion: clean at start and end, dirty during watchdog poll!
            # Calls: [0]=initial check (clean), [1]=first watchdog poll (clean), [2]=second poll (dirty), [3+]=clean.
            poll_seq = [clean_rocm, clean_rocm, dirty_rocm, clean_rocm, clean_rocm, clean_rocm]
            call_idx = {"n": 0}

            def _seq_run(*_a, **_kw):
                i = call_idx["n"]
                call_idx["n"] += 1
                return poll_seq[min(i, len(poll_seq) - 1)]

            with (
                patch("run_experiment.shutil.which", side_effect=lambda cmd: "/usr/bin/rocm-smi" if cmd == "rocm-smi" else None),
                patch("run_experiment.subprocess.run", side_effect=_seq_run),
            ):
                lease_bad = ExclusiveGpuLease(
                    "cuda",
                    require_exclusive=True,
                    lock_path=lock_path,
                    poll_interval_seconds=0.02,
                    stage="intrusion_test",
                )
                with lease_bad:
                    time.sleep(0.08)

                self.assertTrue(lease_bad.report["lease_held_for_full_run"])
                self.assertFalse(lease_bad.report["exclusive_maintained_throughout_run"])
                self.assertFalse(lease_bad.report["exclusive_verified"])
                self.assertIn(888888, lease_bad.report["foreign_pids"])
                self.assertGreaterEqual(len(lease_bad.report["mid_run_intrusions"]), 1)
                self.assertFalse(is_full_run_gpu_reservation_verified(lease_bad.report))
                with self.assertRaises(RuntimeError):
                    lease_bad.raise_if_intruded()

            # 3. Non-zero rocm-smi exit code fails closed (does not masquerade as zero foreign PIDs).
            with (
                patch("run_experiment.shutil.which", side_effect=lambda cmd: "/usr/bin/rocm-smi" if cmd == "rocm-smi" else None),
                patch("run_experiment.subprocess.run", return_value=err_rocm),
            ):
                res_err = check_exclusive_gpu("cuda", require_exclusive=False)
                self.assertFalse(res_err["exclusive_verified"])
                with self.assertRaises(RuntimeError):
                    check_exclusive_gpu("cuda", require_exclusive=True)

    def test_exclusive_gpu_check_rejects_foreign_pid_and_no_helper_arm_omits_binding(self):
        fake_rocm = Mock(stdout="PID\tPROCESS\n999999\tother_worker\n")
        with (
            patch("run_experiment.shutil.which", side_effect=lambda cmd: "/usr/bin/rocm-smi" if cmd == "rocm-smi" else None),
            patch("run_experiment.subprocess.run", return_value=fake_rocm),
        ):
            res = check_exclusive_gpu("cuda", require_exclusive=False)
            self.assertFalse(res["exclusive_verified"])
            self.assertIn(999999, res["foreign_pids"])
            with self.assertRaises(RuntimeError):
                check_exclusive_gpu("cuda", require_exclusive=True)

        # Verify no_helper arm runs cleanly in _run_live_arm with helper_name=None and binding=None.
        now = 0
        budget = ArmBudget(100_000_000, shared_setup_ns=1_000_000, synchronize=lambda: None, clock=lambda: now)
        snap = {"prefix_token_ids": [1], "rng_state": {}, "switch_exposure": {"ordinary_named_fn_arm": "unused"}}
        with (
            patch("run_experiment.adapt_arm_equal_budget", return_value={"tokens_processed": 0, "delta_in": None, "delta_out": None}),
            patch("run_experiment.restore_rng_state"),
            patch("run_experiment._sample_continuation_from_cache", return_value=([7], 1)),
            patch("run_experiment.verify_candidate", return_value={"passed": True, "status": "pass"}) as mock_ver,
        ):
            rec, _ = _run_live_arm(
                "no_helper", DEV_PROBLEMS[0], snap, Mock(), Mock(helper_token_id=259),
                Mock(decode=Mock(return_value="pass")), budget, attempt_cap=1, setup_steps=0,
                learning_rate=0.0, max_new_tokens=4, verifier_timeout=0.05,
            )
            self.assertTrue(rec["solved"])
            self.assertIsNone(mock_ver.call_args.kwargs["helper_name"])
            self.assertIsNone(mock_ver.call_args.kwargs["binding"])
            self.assertFalse(mock_ver.call_args.kwargs["arm_uses_alias"])

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
