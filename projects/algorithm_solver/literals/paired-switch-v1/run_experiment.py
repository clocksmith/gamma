#!/usr/bin/env python3
"""CLI entrypoint for the BITS paired-switch experiment (`paired-switch-v1`).

Subcommands:
  verify-fixture   Build and verify canonical Section 1 `skip_equal` switch point.
  verify-engine    Run Sections 2-3 mechanical & numerical verification on BOTH
                   tied and untied PyTorch `transformers` causal LMs.
  verify-dev-suite Verify all 9 Section 4 development problems, helpers, and
                   switch-time predictor decisions.
  run-live         Run live free-search paired comparison on a user-provisioned
                   local HuggingFace causal LM (`local_files_only=True` default).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from dev_families import DEV_PROBLEMS, get_problem, verify_dev_family_suite
from helpers import HELPER_SPECS, verify_all_helpers
from predictor import predict_switch_benefit, summarize_paired_search_outcomes
from switch_engine import (
    ByteLevelTestTokenizer,
    HelperAliasTokenizer,
    PairedSwitchAdapter,
    PrefillState,
    adapt_arm_equal_budget,
    build_switch_adaptation_sequences,
    build_synthetic_transformer,
    get_peak_rss_bytes,
    run_forced_call_check,
    verify_cache_reuse_and_rebuild_parity,
)
from switch_point import (
    build_switch_point,
    restore_rng_state,
    save_switch_point,
    verify_switch_point_snapshot,
)
from verifier import (
    HELPER_TOKEN_SYMBOL,
    SingleBindRegistry,
    _ALIAS_IDENTIFIER,
    translate_alias_source,
    verify_candidate,
)
from work_budget import ArmBudget, OutOfBudget, positive_nanoseconds


FIXTURE_PATH = HERE / "fixtures" / "skip_equal_switch_point.json"
CONTRACT_PATH = HERE / "rung3_contract.json"


def cmd_verify_fixture(_args: argparse.Namespace) -> int:
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
    problem = get_problem("dup_02_unique_triplets_zero")
    snapshot = build_switch_point(
        problem=problem,
        tokenizer_encode=tok.encode,
        helper_token_id=tok.helper_token_id,
        remaining_attempt_cap=32,
        remaining_token_budget=32 * 384,
        setup_budget_steps=16,
        seed=20261127,
    )
    save_switch_point(snapshot, FIXTURE_PATH)
    loaded = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    check = verify_switch_point_snapshot(loaded)
    print(json.dumps({"fixture_path": str(FIXTURE_PATH), "verification": check}, indent=2))
    return 0


def run_engine_verification(
    *,
    tie_word_embeddings: bool,
    device: str = "cpu",
    setup_budget_steps: int = 12,
) -> dict[str, Any]:
    """Run Sections 2-3 mechanical & numerical checks on a real transformers LlamaForCausalLM."""
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)
    problem = get_problem("dup_02_unique_triplets_zero")
    snapshot = build_switch_point(
        problem=problem,
        tokenizer_encode=tok.encode,
        helper_token_id=tok.helper_token_id,
        remaining_attempt_cap=32,
        remaining_token_budget=32 * 384,
        setup_budget_steps=setup_budget_steps,
        seed=20261127,
    )
    model = build_synthetic_transformer(
        vocab_size=tok.vocab_size,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        tie_word_embeddings=tie_word_embeddings,
        seed=1337,
        device=device,
        dtype=torch.float32,
    )
    adapter = PairedSwitchAdapter(model, helper_token_id=tok.helper_token_id)
    try:
        adapt_examples = build_switch_adaptation_sequences(snapshot, tok.encode)

        arm_reports = {}
        arm_states = {}
        for arm in ("frozen_alias", "score_only_alias", "score_and_input_alias", "ordinary_named_fn"):
            res = adapt_arm_equal_budget(
                adapter,
                arm_name=arm,
                adaptation_examples=adapt_examples,
                setup_budget_steps=setup_budget_steps,
                lr=5e-2,
            )
            arm_states[arm] = res
            arm_reports[arm] = {k: v for k, v in res.items() if k not in ("delta_out", "delta_in")}

        # Confirm equal setup spend between score_only and score_and_input.
        so = arm_reports["score_only_alias"]
        si = arm_reports["score_and_input_alias"]
        equal_spend_ok = (
            so["actual_steps"] == si["actual_steps"] == setup_budget_steps
            and so["forward_passes"] == si["forward_passes"]
            and so["backward_passes"] == si["backward_passes"]
            and so["tokens_processed"] == si["tokens_processed"]
        )

        # Section 3A: forward-only KV-cache reuse + fresh boundary scoring + full rebuild parity.
        cont_text = (
            snapshot["switch_exposure"]["alias_arms"]
            + "\n[ASSISTANT]\ndef unique_zero_triplets(nums):\n    i = <H0>(xs, i)\n    return []\n"
        )
        cont_ids = tok.encode(cont_text)
        cache_check = verify_cache_reuse_and_rebuild_parity(
            adapter,
            prefix_token_ids=snapshot["prefix_token_ids"],
            continuation_token_ids=cont_ids,
            delta_out=arm_states["score_and_input_alias"]["delta_out"],
            delta_in=arm_states["score_and_input_alias"]["delta_in"],
            numerical_tol=1e-4,
        )

        # Section 3B: forced-call isolation check (exact shared output row, toggle only input row).
        pre_call_ids = tok.encode(
            snapshot["switch_exposure"]["alias_arms"].replace(HELPER_TOKEN_SYMBOL, "HELPER_OP")
            + "\n[ASSISTANT]\nj = "
        )
        forced_ops_ids = tok.encode("(xs, i)\n")
        forced_ver_ids = tok.encode(
            "\n[TOOL]\nVERIFIER_ATTEMPT_3: status=fail passed=2/3 first_failure_case=run_of_duplicates\n"
        )
        forced_check = run_forced_call_check(
            adapter,
            prefix_token_ids=snapshot["prefix_token_ids"],
            pre_call_tokens=pre_call_ids,
            forced_operands_and_body_tokens=forced_ops_ids,
            forced_verifier_response_tokens=forced_ver_ids,
            shared_delta_out=arm_states["score_and_input_alias"]["delta_out"],
            adapted_delta_in=arm_states["score_and_input_alias"]["delta_in"],
        )

        all_invariance_ok = all(
            r["invariance"]["backbone_and_other_rows_exact"]
            and r["invariance"]["arm_row_contract_ok"]
            for r in arm_reports.values()
        )
        passed = bool(
            equal_spend_ok
            and all_invariance_ok
            and cache_check["passed"]
            and forced_check["fixture_passed"]
            and forced_check["input_effect_isolated"]
        )
        return {
            "synthetic_mechanical_check_only": True,
            "trained_model_search_claim": False,
            "tie_word_embeddings": tie_word_embeddings,
            "adapter_detected_tied_embeddings": adapter.tied_embeddings,
            "device": device,
            "equal_spend_ok": equal_spend_ok,
            "all_invariance_ok": all_invariance_ok,
            "arms": arm_reports,
            "cache_reuse_check": cache_check,
            "forced_call_check": forced_check,
            "passed": passed,
        }
    finally:
        adapter.close()


def cmd_verify_engine(args: argparse.Namespace) -> int:
    results = {}
    for tied in (True, False):
        key = "tied_embeddings" if tied else "untied_embeddings"
        results[key] = run_engine_verification(
            tie_word_embeddings=tied,
            device=args.device,
            setup_budget_steps=args.setup_steps,
        )
    overall = all(r["passed"] for r in results.values())
    print(json.dumps({"overall_passed": overall, "modes": results}, indent=2))
    return 0 if overall else 1


def cmd_verify_dev_suite(_args: argparse.Namespace) -> int:
    helpers_receipt = verify_all_helpers()
    suite_receipt = verify_dev_family_suite(helper_token_id=259)
    tok = ByteLevelTestTokenizer(helper_symbol=HELPER_TOKEN_SYMBOL, helper_token_id=259)

    pred_rows = []
    for prob in DEV_PROBLEMS:
        for cap in (2, 32):
            snap = build_switch_point(
                problem=prob,
                tokenizer_encode=tok.encode,
                helper_token_id=tok.helper_token_id,
                remaining_attempt_cap=cap,
                remaining_token_budget=cap * 384,
                setup_budget_steps=16,
                seed=20261127,
            )
            pred = predict_switch_benefit(snap)
            pred_rows.append(
                {
                    "problem_id": prob["problem_id"],
                    "family": prob["family"],
                    "utility_regime": prob["utility_regime"],
                    "attempt_cap": cap,
                    "decision": pred.decision,
                    "symptom_match_score": pred.symptom_match_score,
                    "predicted_net_benefit": pred.predicted_net_benefit,
                }
            )

    useful_rows = [r for r in pred_rows if r["utility_regime"] != "irrelevant_decoy"]
    decoy_rows = [r for r in pred_rows if r["utility_regime"] == "irrelevant_decoy"]
    useful_adapt_rate = sum(1 for r in useful_rows if r["decision"] == "ADAPT") / len(useful_rows)
    decoy_skip_rate = sum(1 for r in decoy_rows if r["decision"] == "SKIP") / len(decoy_rows)

    out = {
        "helpers_verified": list(helpers_receipt.keys()),
        "suite": suite_receipt,
        "switch_predictor_offline_check": {
            "useful_adapt_rate": useful_adapt_rate,
            "decoy_skip_rate": decoy_skip_rate,
            "rows": pred_rows,
        },
    }
    print(json.dumps(out, indent=2))
    return 0


_CODE_BLOCK_RE = re.compile(r"```(?:python|py|python3)?\s*\n(.*?)```", re.S)


def _extract_python_code(text: str) -> str:
    blocks = _CODE_BLOCK_RE.findall(text)
    if blocks:
        return blocks[-1].strip() + "\n"
    return text.strip() + "\n"


def _sample_continuation_from_cache(
    adapter: PairedSwitchAdapter,
    *,
    past_key_values: Any,
    start_pos: int,
    prompt_suffix_ids: list[int],
    max_new_tokens: int,
    eos_token_id: int | None,
    temperature: float,
    budget: ArmBudget,
) -> tuple[list[int], int]:
    """Generate one candidate attempt forward-only from a cloned KV cache."""
    if prompt_suffix_ids:
        logits_seq, cache = adapter.forward_from_cache(
            past_key_values, start_pos=start_pos, new_token_ids=prompt_suffix_ids
        )
        next_logits = logits_seq[:, -1, :]
        pos = start_pos + len(prompt_suffix_ids)
    else:
        raise ValueError("prompt_suffix_ids must be non-empty")

    generated: list[int] = []
    with torch.no_grad():
        for _ in range(max_new_tokens):
            budget.checkpoint()
            if temperature <= 0.0:
                tok_id = int(next_logits.argmax(dim=-1).item())
            else:
                probs = torch.softmax(next_logits.to(torch.float32) / temperature, dim=-1)
                tok_id = int(torch.multinomial(probs, num_samples=1).item())
            generated.append(tok_id)
            if eos_token_id is not None and tok_id == eos_token_id:
                break
            inp = torch.tensor([[tok_id]], dtype=torch.long, device=adapter.device)
            pos_ids = torch.tensor([[pos]], dtype=torch.long, device=adapter.device)
            budget.checkpoint()
            out = adapter.model(
                input_ids=inp,
                position_ids=pos_ids,
                past_key_values=cache,
                use_cache=True,
            )
            cache = out.past_key_values
            next_logits = out.logits[:, -1, :]
            pos += 1
    return generated, len(prompt_suffix_ids) + len(generated)


def _device_synchronizer(device: torch.device) -> Callable[[], None]:
    if device.type == "cuda":
        return lambda: torch.cuda.synchronize(device)
    if device.type == "mps":
        return torch.mps.synchronize
    return lambda: None


def verify_helper_token_roundtrip(alias_tokenizer: HelperAliasTokenizer) -> dict[str, Any]:
    """Verify `<H0>` encodes to one exact ID and decodes to an executable helper call."""
    sym = alias_tokenizer.helper_symbol
    hid = alias_tokenizer.helper_token_id
    encoded_sym = alias_tokenizer.encode(sym)
    if encoded_sym != [hid]:
        raise RuntimeError(
            f"Helper symbol {sym!r} must encode to single token ID [{hid}], got {encoded_sym!r}"
        )
    decoded_sym = alias_tokenizer.decode([hid], skip_special_tokens=True)
    if decoded_sym != sym:
        raise RuntimeError(
            f"Reserved token ID {hid} must decode to {sym!r}, got {decoded_sym!r}"
        )
    probe_src = f"def _bits_h0_probe(xs, i):\n    j = {sym}(xs, i)\n    return j\n"
    probe_ids = alias_tokenizer.encode(probe_src)
    hid_count = sum(1 for tid in probe_ids if tid == hid)
    if hid_count != 1:
        raise RuntimeError(
            f"Expected reserved token ID {hid} once in encoded probe source, found {hid_count}"
        )
    roundtrip_src = alias_tokenizer.decode(probe_ids, skip_special_tokens=True)
    binding = SingleBindRegistry().bind_once("skip_equal", hid, sym)
    lowered = translate_alias_source(roundtrip_src, binding, arm_uses_alias=True)
    calls = [0]
    impl = HELPER_SPECS["skip_equal"].implementation

    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        return impl(*args, **kwargs)

    ns: dict[str, Any] = {_ALIAS_IDENTIFIER: _wrapped}
    exec(compile(lowered, "<h0-probe>", "exec"), ns)
    actual = ns["_bits_h0_probe"]([2, 2, 5], 0)
    if actual != 2 or calls[0] != 1:
        raise RuntimeError(
            f"Decoded helper token {sym!r} (id={hid}) did not execute bound helper cleanly: "
            f"actual={actual!r}, calls={calls[0]}"
        )
    return {
        "helper_symbol": sym,
        "helper_token_id": hid,
        "encoded_symbol_ids": encoded_sym,
        "decoded_symbol": decoded_sym,
        "probe_token_id_count": hid_count,
        "probe_executable_passed": True,
        "probe_runtime_helper_calls": calls[0],
    }


def _run_live_arm(
    arm: str,
    problem: dict[str, Any],
    snapshot: dict[str, Any],
    prefill: PrefillState | None,
    adapter: PairedSwitchAdapter,
    tokenizer: Any,
    budget: ArmBudget,
    *,
    attempt_cap: int,
    setup_steps: int,
    learning_rate: float,
    max_new_tokens: int,
    verifier_timeout: float,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    alias = arm != "ordinary_named_fn"
    verify_ns = positive_nanoseconds(verifier_timeout)
    state = None
    solved = False
    status = "attempt_cap"
    blocked_phase = None
    attempts = checks = calls = generation_tokens = 0
    verifier_statuses: dict[str, int] = {}
    partial_generation = False

    alias_tokenizer = (
        tokenizer
        if isinstance(tokenizer, HelperAliasTokenizer)
        else HelperAliasTokenizer(
            tokenizer,
            helper_token_id=adapter.helper_token_id,
            helper_symbol=HELPER_TOKEN_SYMBOL,
        )
    )

    try:
        budget.enter("setup")
        binding = (
            SingleBindRegistry().bind_once(problem["helper_name"], adapter.helper_token_id)
            if alias else None
        )

        def encode(text: str) -> list[int]:
            return alias_tokenizer.encode(text, add_special_tokens=False)

        examples = (
            build_switch_adaptation_sequences(snapshot, encode)
            if arm in ("score_only_alias", "score_and_input_alias") else []
        )
        budget.checkpoint()
        state = adapt_arm_equal_budget(
            adapter, arm_name=arm, adaptation_examples=examples, setup_budget_steps=setup_steps,
            lr=learning_rate, checkpoint=budget.checkpoint,
        )
        budget.checkpoint()
        adapter.set_deltas(state["delta_out"], state["delta_in"])
        restore_rng_state(snapshot["rng_state"])
        exposure_key = "alias_arms" if alias else "ordinary_named_fn_arm"
        exposure = snapshot["switch_exposure"][exposure_key]
        suffix = encode(f"[SYSTEM_SWITCH]\n{exposure}\n[ASSISTANT]\n```python\n")
        cases = problem["public_cases"] + problem["hidden_cases"]
        for attempt in range(attempt_cap):
            # An attempt cannot yield a verified solution without one full verifier window.
            budget.enter("generation", reserve_ns=verify_ns)
            attempts += 1
            partial_generation = True
            ids, tokens = _sample_continuation_from_cache(
                adapter, past_key_values=prefill.past_key_values,
                start_pos=len(snapshot["prefix_token_ids"]), prompt_suffix_ids=suffix,
                max_new_tokens=max_new_tokens, eos_token_id=alias_tokenizer.eos_token_id,
                temperature=0.0 if attempt == 0 else 0.7, budget=budget,
            )
            generation_tokens += tokens
            partial_generation = False
            source = _extract_python_code(alias_tokenizer.decode(ids, skip_special_tokens=True))
            budget.enter("verification", reserve_ns=verify_ns)
            checks += 1
            verdict = verify_candidate(
                source, entry_point=problem["entry_point"], cases=cases, helper_name=problem["helper_name"],
                binding=binding, arm_uses_alias=alias, timeout_seconds=verifier_timeout,
                deadline_ns=budget.deadline,
            )
            calls += int(verdict.get("syntactic_helper_calls", 0))
            status = verdict["status"]
            verifier_statuses[status] = verifier_statuses.get(status, 0) + 1
            if verdict["passed"]:
                solved = True
                break
    except OutOfBudget as exc:
        blocked_phase = str(exc)

    spent_ns = budget.finish()
    if spent_ns > budget.limit_ns:
        blocked_phase = blocked_phase or budget.phase
    if blocked_phase is not None:
        solved = False
        status = "budget_exhausted"

    seconds = spent_ns / 1e9
    record = {
        "problem_id": problem["problem_id"], "family": problem["family"],
        "utility_regime": problem["utility_regime"],
        "switch_point_id": f"{problem['problem_id']}@cap{attempt_cap}", "attempt_cap": attempt_cap,
        "arm": arm, "solved": solved, "status": status, "attempts_started": attempts,
        "failed_attempts": attempts - int(solved),
        "verifier_calls": checks, "verifier_statuses": verifier_statuses, "helper_calls": calls,
        "setup_tokens": state["tokens_processed"] if state is not None else None,
        "generation_tokens_completed_attempts": generation_tokens, "interrupted_generation": partial_generation,
        "total_work_units": seconds, "elapsed_seconds": seconds,
        "work_to_first_verified": seconds if solved else None,
        "budget_limit_ns": budget.limit_ns, "phase_ns": budget.phase_ns,
        "remaining_ns": max(0, budget.limit_ns - spent_ns),
        "overrun_ns": max(0, spent_ns - budget.limit_ns), "blocked_phase": blocked_phase,
        "peak_memory_bytes": get_peak_rss_bytes(),
    }
    return record, state


def cmd_run_live(args: argparse.Namespace) -> int:
    """Run live free-search paired comparison on a user-provisioned HF causal LM."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if args.split == "sealed" and not args.sealed_problems_json:
        raise SystemExit("Refusing sealed run without explicit --sealed-problems-json")

    local_only = not args.allow_download
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32
    limit_ns = positive_nanoseconds(args.arm_budget_seconds)
    preparation_start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=local_only)
    if HELPER_TOKEN_SYMBOL not in tokenizer.get_vocab() and args.reserved_token_id is None:
        raise SystemExit(
            f"Model tokenizer does not reserve {HELPER_TOKEN_SYMBOL}; select a provisioned "
            f"unused special token ID via --reserved-token-id or reserve {HELPER_TOKEN_SYMBOL} "
            f"before creating the switch point."
        )

    helper_token_id = (
        int(args.reserved_token_id)
        if args.reserved_token_id is not None
        else int(tokenizer.convert_tokens_to_ids(HELPER_TOKEN_SYMBOL))
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=dtype,
        local_files_only=local_only,
    ).to(args.device).eval()

    problems = (
        DEV_PROBLEMS
        if args.split == "dev"
        else json.loads(Path(args.sealed_problems_json).read_text(encoding="utf-8"))
    )
    caps = [int(x.strip()) for x in args.attempt_caps.split(",") if x.strip()]
    setup_steps = int(args.setup_steps)
    max_new_tokens = int(contract["search_budgets"]["max_new_tokens_per_attempt"])
    timeout_s = float(contract["search_budgets"]["verifier_timeout_seconds"])

    adapter = PairedSwitchAdapter(model, helper_token_id=helper_token_id)
    alias_tokenizer = HelperAliasTokenizer(
        tokenizer,
        helper_token_id=helper_token_id,
        helper_symbol=HELPER_TOKEN_SYMBOL,
        vocab_size=min(adapter.vocab_size, int(adapter.lm_head.weight.shape[0])),
    )
    roundtrip_receipt = verify_helper_token_roundtrip(alias_tokenizer)
    sync = _device_synchronizer(adapter.device)
    sync()
    preparation_seconds = time.perf_counter() - preparation_start
    records: list[dict[str, Any]] = []
    gate_receipts: list[dict[str, Any]] = []

    try:
        for prob in problems:
            for cap in caps:
                snapshot_start = time.perf_counter()
                snap = build_switch_point(
                    problem=prob,
                    tokenizer_encode=lambda s: alias_tokenizer.encode(s, add_special_tokens=False),
                    helper_token_id=helper_token_id,
                    remaining_attempt_cap=cap,
                    remaining_token_budget=cap * max_new_tokens,
                    setup_budget_steps=setup_steps,
                    seed=20261127,
                )
                # The snapshot supplies the completed search history and the fixed helper.
                # Measure shared switch work once and debit its full cost to every continuation.
                snapshot_seconds = time.perf_counter() - snapshot_start
                shared = ArmBudget(limit_ns, synchronize=sync)
                pred = predict_switch_benefit(snap)
                prefill = None
                try:
                    adapter.set_deltas(None, None)
                    shared.checkpoint()
                    prefill = adapter.prefill_prefix(snap["prefix_token_ids"])
                except OutOfBudget:
                    pass
                shared_ns = shared.finish()
                joint_state = None
                for entry in contract["arms"]:
                    arm = entry["name"]
                    budget = ArmBudget(limit_ns, shared_setup_ns=shared_ns, synchronize=sync)
                    record, state = _run_live_arm(
                        arm, prob, snap, prefill, adapter, alias_tokenizer, budget,
                        attempt_cap=cap, setup_steps=setup_steps,
                        learning_rate=float(contract["adaptation_policy"]["learning_rate"]),
                        max_new_tokens=max_new_tokens, verifier_timeout=timeout_s,
                    )
                    records.append(record)
                    if arm == "score_and_input_alias":
                        joint_state = state

                # Offline diagnostic, performed only after paired search outcomes are fixed.
                gate = {
                    "problem_id": prob["problem_id"], "attempt_cap": cap,
                    "switch_prediction": pred.decision,
                    "snapshot_preparation_seconds": snapshot_seconds,
                    "forced_call": {"status": "joint_setup_incomplete", "fixture_passed": False},
                }
                if joint_state is not None:
                    started = time.perf_counter()
                    fc = run_forced_call_check(
                        adapter, prefix_token_ids=snap["prefix_token_ids"],
                        pre_call_tokens=alias_tokenizer.encode(
                            snap["switch_exposure"]["alias_arms"].replace(HELPER_TOKEN_SYMBOL, "HELPER_OP")
                            + "\nj = ", add_special_tokens=False,
                        ),
                        forced_operands_and_body_tokens=alias_tokenizer.encode("(xs, i)\n", add_special_tokens=False),
                        forced_verifier_response_tokens=alias_tokenizer.encode(
                            "\n[TOOL]\nVERIFIER: retry\n", add_special_tokens=False,
                        ),
                        shared_delta_out=joint_state["delta_out"], adapted_delta_in=joint_state["delta_in"],
                    )
                    sync()
                    gate.update(forced_call=fc, diagnostic_seconds=time.perf_counter() - started)
                    if not fc["fixture_passed"]:
                        raise RuntimeError(f"Forced-call pre-call gate FAILED on {prob['problem_id']}: {fc}")
                gate_receipts.append(gate)
    finally:
        adapter.close()

    summary = summarize_paired_search_outcomes(records)
    payload = {
        "schema_version": "bits-paired-switch-live-receipt-v2",
        "work_unit": "synchronized_elapsed_seconds",
        "resident_model_preparation_seconds": preparation_seconds,
        "budget_limit_ns_per_arm": limit_ns,
        "verifier_reservation_ns": positive_nanoseconds(timeout_s),
        "helper_token_roundtrip": roundtrip_receipt,
        "model": args.model,
        "device": args.device,
        "dtype": args.dtype,
        "split": args.split,
        "attempt_caps": caps,
        "setup_steps": setup_steps,
        "gate_receipts": gate_receipts,
        "summary": summary,
        "records": records,
    }
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BITS paired-switch experiment runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fix = sub.add_parser("verify-fixture", help="Build and verify canonical Section 1 skip_equal fixture")
    p_fix.set_defaults(func=cmd_verify_fixture)

    p_eng = sub.add_parser("verify-engine", help="Verify Sections 2-3 on tied and untied transformers LMs")
    p_eng.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_eng.add_argument("--setup-steps", type=int, default=12)
    p_eng.set_defaults(func=cmd_verify_engine)

    p_dev = sub.add_parser("verify-dev-suite", help="Verify Section 4 development families, helpers, and predictor")
    p_dev.set_defaults(func=cmd_verify_dev_suite)

    p_live = sub.add_parser("run-live", help="Run live free-search paired comparison on provisioned HF model")
    p_live.add_argument("--model", required=True, help="Local HF model directory or authorized repo id")
    p_live.add_argument("--device", default="cpu", choices=["cpu", "mps", "cuda"])
    p_live.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"])
    p_live.add_argument("--split", default="dev", choices=["dev", "sealed"])
    p_live.add_argument("--sealed-problems-json", default=None)
    p_live.add_argument("--reserved-token-id", type=int, default=None)
    p_live.add_argument("--attempt-caps", default="2,32")
    p_live.add_argument("--setup-steps", type=int, default=16)
    p_live.add_argument("--arm-budget-seconds", required=True, type=float,
                        help="Identical total elapsed-time allowance per arm, from switch through verification")
    p_live.add_argument("--allow-download", action="store_true", help="Explicitly authorize HF download")
    p_live.add_argument("--output", required=True)
    p_live.set_defaults(func=cmd_run_live)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
