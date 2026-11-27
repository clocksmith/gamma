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
    PairedSwitchAdapter,
    adapt_arm_equal_budget,
    build_switch_adaptation_sequences,
    build_synthetic_transformer,
    clone_kv_cache,
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
from verifier import HELPER_TOKEN_SYMBOL, SingleBindRegistry, verify_candidate


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


def cmd_run_live(args: argparse.Namespace) -> int:
    """Run live free-search paired comparison on a user-provisioned HF causal LM."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if args.split == "sealed" and not args.sealed_problems_json:
        raise SystemExit("Refusing sealed run without explicit --sealed-problems-json")

    local_only = not args.allow_download
    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32
    tol = (
        contract["numerical_verification_gates"]["rebuild_parity_tol_bf16"]
        if dtype == torch.bfloat16
        else contract["numerical_verification_gates"]["rebuild_parity_tol_fp32"]
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=local_only)
    if HELPER_TOKEN_SYMBOL not in tokenizer.get_vocab():
        raise SystemExit(
            f"Model tokenizer does not reserve {HELPER_TOKEN_SYMBOL}; select a provisioned "
            f"unused special token ID via --reserved-token-id or reserve {HELPER_TOKEN_SYMBOL} "
            f"before creating the switch point."
        ) if args.reserved_token_id is None else None

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
    records: list[dict[str, Any]] = []
    gate_receipts: list[dict[str, Any]] = []

    try:
        for prob in problems:
            for cap in caps:
                snap = build_switch_point(
                    problem=prob,
                    tokenizer_encode=lambda s: tokenizer.encode(s, add_special_tokens=False),
                    helper_token_id=helper_token_id,
                    remaining_attempt_cap=cap,
                    remaining_token_budget=cap * max_new_tokens,
                    setup_budget_steps=setup_steps,
                    seed=20261127,
                )
                pred = predict_switch_benefit(snap)
                adapt_examples = build_switch_adaptation_sequences(
                    snap, lambda s: tokenizer.encode(s, add_special_tokens=False)
                )

                # Prefill saved prefix once (verified absent of helper_token_id).
                adapter.set_deltas(None, None)
                prefill = adapter.prefill_prefix(snap["prefix_token_ids"])

                # Adapt score_only and score_and_input under equal budget.
                arm_states: dict[str, dict[str, Any]] = {}
                for arm in ("frozen_alias", "score_only_alias", "score_and_input_alias", "ordinary_named_fn"):
                    arm_states[arm] = adapt_arm_equal_budget(
                        adapter,
                        arm_name=arm,
                        adaptation_examples=adapt_examples,
                        setup_budget_steps=setup_steps,
                        lr=float(contract["adaptation_policy"]["learning_rate"]),
                    )

                # Mandatory Section 3 gates on this live model & switch point before free search.
                pre_call_ids = tokenizer.encode(
                    snap["switch_exposure"]["alias_arms"].replace(HELPER_TOKEN_SYMBOL, "HELPER_OP")
                    + "\nj = ",
                    add_special_tokens=False,
                )
                forced_ops_ids = tokenizer.encode("(xs, i)\n", add_special_tokens=False)
                forced_ver_ids = tokenizer.encode("\n[TOOL]\nVERIFIER: retry\n", add_special_tokens=False)
                fc = run_forced_call_check(
                    adapter,
                    prefix_token_ids=snap["prefix_token_ids"],
                    pre_call_tokens=pre_call_ids,
                    forced_operands_and_body_tokens=forced_ops_ids,
                    forced_verifier_response_tokens=forced_ver_ids,
                    shared_delta_out=arm_states["score_and_input_alias"]["delta_out"],
                    adapted_delta_in=arm_states["score_and_input_alias"]["delta_in"],
                )
                if not fc["fixture_passed"]:
                    raise RuntimeError(
                        f"Forced-call pre-call gate FAILED on {prob['problem_id']}: {fc}"
                    )
                gate_receipts.append(
                    {
                        "problem_id": prob["problem_id"],
                        "attempt_cap": cap,
                        "forced_call": fc,
                        "switch_prediction": pred.decision,
                    }
                )

                # Free search across all four arms, paired by (problem_id, switch_point_id).
                switch_point_id = f"{prob['problem_id']}@cap{cap}"
                all_cases = prob["public_cases"] + prob["hidden_cases"]
                for arm in ("frozen_alias", "score_only_alias", "score_and_input_alias", "ordinary_named_fn"):
                    arm_uses_alias = arm != "ordinary_named_fn"
                    reg = SingleBindRegistry()
                    binding = (
                        reg.bind_once(prob["helper_name"], helper_token_id, HELPER_TOKEN_SYMBOL)
                        if arm_uses_alias
                        else None
                    )
                    st = arm_states[arm]
                    adapter.set_deltas(st["delta_out"], st["delta_in"])
                    restore_rng_state(snap["rng_state"])

                    exposure = (
                        snap["switch_exposure"]["alias_arms"]
                        if arm_uses_alias
                        else snap["switch_exposure"]["ordinary_named_fn_arm"]
                    )
                    suffix_ids = tokenizer.encode(
                        f"[SYSTEM_SWITCH]\n{exposure}\n[ASSISTANT]\n```python\n",
                        add_special_tokens=False,
                    )

                    started = time.perf_counter()
                    solved = False
                    status = "budget_exhausted"
                    failed_attempts = 0
                    helper_calls = 0
                    gen_tokens = 0
                    work_to_first = None
                    setup_work_tokens = int(st["tokens_processed"])

                    for att_idx in range(1, cap + 1):
                        temp = 0.0 if att_idx == 1 else 0.7
                        gen_ids, step_toks = _sample_continuation_from_cache(
                            adapter,
                            past_key_values=prefill.past_key_values,
                            start_pos=len(snap["prefix_token_ids"]),
                            prompt_suffix_ids=suffix_ids,
                            max_new_tokens=max_new_tokens,
                            eos_token_id=tokenizer.eos_token_id,
                            temperature=temp,
                        )
                        gen_tokens += step_toks
                        cand_text = tokenizer.decode(gen_ids, skip_special_tokens=False)
                        cand_src = _extract_python_code(cand_text)
                        verdict = verify_candidate(
                            cand_src,
                            entry_point=prob["entry_point"],
                            cases=all_cases,
                            helper_name=prob["helper_name"],
                            binding=binding,
                            arm_uses_alias=arm_uses_alias,
                            timeout_seconds=timeout_s,
                        )
                        helper_calls += int(verdict.get("syntactic_helper_calls", 0))
                        if verdict["passed"]:
                            solved = True
                            status = "pass"
                            work_to_first = setup_work_tokens + gen_tokens
                            break
                        failed_attempts += 1
                        status = str(verdict["status"])

                    records.append(
                        {
                            "problem_id": prob["problem_id"],
                            "family": prob["family"],
                            "utility_regime": prob["utility_regime"],
                            "switch_point_id": switch_point_id,
                            "attempt_cap": cap,
                            "arm": arm,
                            "solved": solved,
                            "status": status,
                            "failed_attempts": failed_attempts,
                            "helper_calls": helper_calls,
                            "setup_tokens": setup_work_tokens,
                            "generation_tokens": gen_tokens,
                            "total_work_units": setup_work_tokens + gen_tokens,
                            "work_to_first_verified": work_to_first,
                            "elapsed_seconds": round(time.perf_counter() - started + st["wall_seconds"], 4),
                            "peak_memory_bytes": get_peak_rss_bytes(),
                        }
                    )
    finally:
        adapter.close()

    summary = summarize_paired_search_outcomes(records)
    payload = {
        "schema_version": "bits-paired-switch-live-receipt-v1",
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
    p_live.add_argument("--allow-download", action="store_true", help="Explicitly authorize HF download")
    p_live.add_argument("--output", required=True)
    p_live.set_defaults(func=cmd_run_live)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
