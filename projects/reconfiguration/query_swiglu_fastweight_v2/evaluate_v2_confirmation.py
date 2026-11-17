"""Frozen unseen confirmation runner (`v2`, Item 4) with `R = 3` repeated latency measurements.

Pre-registered success criteria written to `.protocol.json` BEFORE any task executes:
1. Paired quality gain over `base`: `focal_wins > control_wins` AND two-sided McNemar `p < 0.05`.
2. Paired quality gain over the strongest `matched_compute` control (`max(split2pass, full2pass)`):
   `focal_wins > control_wins` AND two-sided McNemar `p < 0.05`.
3. Paired quality gain over `wrong_context` and `random` controls (`p < 0.01`), plus `0.0` logit diff on `zero`.
4. Repeated latency (`R = 3` timed passes per task on `base` and `focal_fastweight`):
   mean `setup_ms < 5.0%` of `base` total latency, and `focal` mean total latency <= strongest `matched_compute` control.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import time
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

THIS_DIR = Path(__file__).resolve().parent
V1_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v1"
for d in (THIS_DIR, V1_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from score_receipts import exact_mcnemar_two_sided_p, is_equivalent_output
from tasks_v2 import build_v2_unseen_tasks
from transforms_v2 import (
    FastWeightAdapterV2,
    derive_fastweight_v2,
    extract_query_features_for_donor_v2,
    make_random_adapter_v2,
    make_zero_adapter_v2,
)


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def check_gpu_processes() -> list[str]:
    out = subprocess.check_output(["ps", "-Ao", "pid,pcpu,pmem,etime,command"], text=True)
    my_pid = str(os.getpid())
    return [
        ln.strip()
        for ln in out.splitlines()
        if any(k in ln for k in ("flash-native", "native-whole-service", "evaluate_doppler")) and my_pid not in ln
    ]


def percentile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, round(q * (len(s) - 1))))
    return float(s[idx])


def run_single_pass(
    model,
    prompt_ids: torch.Tensor,
    stop_ids: set[int],
    nl_id: int,
    arm_mode: str = "base",
    c_len: int | None = None,
    donor_ad: FastWeightAdapterV2 | None = None,
    rand_seed: int = 0,
    max_new: int = 16,
) -> dict[str, Any]:
    W_lm = model.lm_head.weight
    E_tok = model.model.embed_tokens.weight

    torch.mps.synchronize()
    t0 = time.monotonic()
    out = model.model(input_ids=prompt_ids, use_cache=True, return_dict=True)
    hl_all = out.last_hidden_state[0]
    cache = out.past_key_values

    setup_s = 0.0
    step_deltas: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    logical_b = 0

    if arm_mode != "base":
        torch.mps.synchronize()
        ts = time.monotonic()
        if arm_mode == "donor":
            assert donor_ad is not None
            xq_d = extract_query_features_for_donor_v2(donor_ad, prompt_ids, nl_id, E_tok, hl_all)
            if xq_d is not None:
                step_deltas = donor_ad.evaluate_query(xq_d)
            logical_b = donor_ad.logical_bytes
        else:
            assert c_len is not None
            ad, xq = derive_fastweight_v2(prompt_ids, c_len, nl_id, E_tok, hl_all, W_lm)
            if arm_mode == "zero":
                ad = make_zero_adapter_v2(ad)
            elif arm_mode == "random":
                ad = make_random_adapter_v2(ad, seed=rand_seed)
            logical_b = ad.logical_bytes
            if xq is not None:
                step_deltas = ad.evaluate_query(xq)
        torch.mps.synchronize()
        setup_s = time.monotonic() - ts

    def logits_at(cur_hl_bf16: torch.Tensor, step_k: int) -> torch.Tensor:
        lf = model.lm_head(cur_hl_bf16.unsqueeze(0)).squeeze(0).float()
        if step_k in step_deltas:
            u_t, dv = step_deltas[step_k]
            if dv.abs().max().item() > 0.0:
                lf = lf.clone()
                lf.index_add_(0, u_t, dv.float())
        return lf

    l0_f = logits_at(hl_all[-1], 0)
    first_sample = l0_f[:64].detach().cpu()
    nid = int(l0_f.argmax(dim=-1).item())
    sum_lp = float((l0_f[nid] - torch.logsumexp(l0_f, dim=-1)).item())
    nxt = torch.tensor([[nid]], device=prompt_ids.device, dtype=torch.long)
    gen = [nid]
    torch.mps.synchronize()
    t_first = time.monotonic()

    step_k = 1
    while len(gen) < max_new and gen[-1] not in stop_ids:
        r_s = model.model(input_ids=nxt, past_key_values=cache, use_cache=True, return_dict=True)
        cache = r_s.past_key_values
        lk_f = logits_at(r_s.last_hidden_state[0, -1], step_k)
        nid = int(lk_f.argmax(dim=-1).item())
        sum_lp += float((lk_f[nid] - torch.logsumexp(lk_f, dim=-1)).item())
        nxt = torch.tensor([[nid]], device=prompt_ids.device, dtype=torch.long)
        gen.append(nid)
        step_k += 1

    torch.mps.synchronize()
    t_end = time.monotonic()
    return {
        "generated_ids": gen,
        "mean_logprob": sum_lp / max(1, len(gen)),
        "first_logits_sample": first_sample,
        "setup_ms": setup_s * 1000.0,
        "first_token_ms": (t_first - t0) * 1000.0,
        "decode_ms": (t_end - t_first) * 1000.0,
        "total_ms": (t_end - t0) * 1000.0,
        "logical_bytes": logical_b,
    }


def derive_donor_v2(model, donor_ids: torch.Tensor, donor_c_len: int, nl_id: int) -> tuple[FastWeightAdapterV2, float]:
    torch.mps.synchronize()
    t0 = time.monotonic()
    out = model.model(input_ids=donor_ids, use_cache=False, return_dict=True)
    ad, _ = derive_fastweight_v2(
        donor_ids, donor_c_len, nl_id, model.model.embed_tokens.weight, out.last_hidden_state[0], model.lm_head.weight
    )
    torch.mps.synchronize()
    return ad, (time.monotonic() - t0) * 1000.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=970001)
    ap.add_argument("--count-per-domain", type=int, default=16)
    ap.add_argument("--latency-repeats", type=int, default=3)
    args = ap.parse_args()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    pre_procs = check_gpu_processes()

    hashes = {
        "tasks_v2.py": file_sha256(THIS_DIR / "tasks_v2.py"),
        "transforms_v2.py": file_sha256(THIS_DIR / "transforms_v2.py"),
        "score_receipts.py": file_sha256(V1_DIR / "score_receipts.py"),
        "evaluate_v2_confirmation.py": file_sha256(THIS_DIR / "evaluate_v2_confirmation.py"),
    }
    success_criteria = {
        "focal_vs_base_mcnemar_p_lt": 0.05,
        "focal_vs_strongest_matched_compute_mcnemar_p_lt": 0.05,
        "focal_vs_wrong_context_mcnemar_p_lt": 0.01,
        "focal_vs_random_mcnemar_p_lt": 0.01,
        "mean_setup_pct_of_base_lt": 5.0,
        "latency_repeats_per_task": args.latency_repeats,
    }
    args.output_json.with_suffix(".protocol.json").write_text(json.dumps({
        "schema": "gamma.reconfiguration.query_swiglu_fastweight_v2.protocol/v1",
        "seed": args.seed,
        "count_per_domain": args.count_per_domain,
        "code_sha256": hashes,
        "pre_registered_success_criteria": success_criteria,
    }, indent=2))

    tok = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False, fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).to("mps").eval()
    nl_id = tok.encode("\n", add_special_tokens=False)[0]
    stop_ids = {tok.eos_token_id, nl_id}
    canary_before = float(model.lm_head.weight.detach().cpu().float().norm().item())

    tasks = build_v2_unseen_tasks(seed=args.seed, count_per_domain=args.count_per_domain)
    for t in tasks:
        c_ids = tok.encode(t["context_text"], add_special_tokens=False)
        f_ids = tok.encode(t["prompt"], add_special_tokens=False)
        assert f_ids[: len(c_ids)] == c_ids
        t["c_ids"] = c_ids
        t["f_ids"] = f_ids
        t["ha_ids"] = tok.encode(t["half_a_prompt"], add_special_tokens=False)
        t["hb_ids"] = tok.encode(t["half_b_prompt"], add_special_tokens=False)

    by_dom: dict[str, list[dict[str, Any]]] = {}
    for t in tasks:
        by_dom.setdefault(t["domain"], []).append(t)

    rows = []
    R = int(args.latency_repeats)
    with torch.inference_mode():
        warm = torch.tensor([[nl_id] * 24], device="mps", dtype=torch.long)
        _ = run_single_pass(model, warm, stop_ids, nl_id, arm_mode="base", max_new=2)

        for dom, d_tasks in by_dom.items():
            n_d = len(d_tasks)
            for i, t in enumerate(d_tasks):
                donor_t = d_tasks[(i + 1) % n_d]
                f_ids = torch.tensor([t["f_ids"]], device="mps", dtype=torch.long)
                c_len = len(t["c_ids"])

                # R=3 repeated timed measurements on `base` and `focal_fastweight` (interleaved to cancel drift!)
                b_runs = []
                f_runs = []
                for _ in range(R):
                    b_runs.append(run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="base"))
                    f_runs.append(run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="focal", c_len=c_len))
                # Verify deterministic output stability across all R repeats
                assert all(x["generated_ids"] == b_runs[0]["generated_ids"] for x in b_runs)
                assert all(x["generated_ids"] == f_runs[0]["generated_ids"] for x in f_runs)

                def agg_repeats(runs: list[dict[str, Any]]) -> dict[str, Any]:
                    s_ms = [x["setup_ms"] for x in runs]
                    ft_ms = [x["first_token_ms"] for x in runs]
                    dc_ms = [x["decode_ms"] for x in runs]
                    tt_ms = [x["total_ms"] for x in runs]
                    return {
                        "generated_ids": runs[0]["generated_ids"],
                        "first_logits_sample": runs[0]["first_logits_sample"],
                        "setup_ms": statistics.mean(s_ms),
                        "setup_ms_repeats": s_ms,
                        "first_token_ms": statistics.mean(ft_ms),
                        "decode_ms": statistics.mean(dc_ms),
                        "total_ms": statistics.mean(tt_ms),
                        "total_ms_repeats": tt_ms,
                        "total_ms_std": statistics.pstdev(tt_ms),
                        "logical_bytes": runs[0]["logical_bytes"],
                    }

                rb = agg_repeats(b_runs)
                rf = agg_repeats(f_runs)

                rz = run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="zero", c_len=c_len)
                assert float((rb["first_logits_sample"] - rz["first_logits_sample"]).abs().max().item()) == 0.0

                d_ids = torch.tensor([donor_t["f_ids"]], device="mps", dtype=torch.long)
                donor_ad, donor_ms = derive_donor_v2(model, d_ids, len(donor_t["c_ids"]), nl_id)
                rw = run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="donor", donor_ad=donor_ad)
                rw["donor_setup_ms"] = donor_ms
                rw["total_ms"] += donor_ms

                rr = run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="random", c_len=c_len, rand_seed=980000 + i)

                ha_ids = torch.tensor([t["ha_ids"]], device="mps", dtype=torch.long)
                hb_ids = torch.tensor([t["hb_ids"]], device="mps", dtype=torch.long)
                ra = run_single_pass(model, ha_ids, stop_ids, nl_id, arm_mode="base")
                rb2 = run_single_pass(model, hb_ids, stop_ids, nl_id, arm_mode="base")
                ps = ra if ra["mean_logprob"] >= rb2["mean_logprob"] else rb2
                rsplit = {
                    "generated_ids": ps["generated_ids"],
                    "setup_ms": 0.0,
                    "first_token_ms": ra["first_token_ms"] + rb2["first_token_ms"],
                    "decode_ms": ra["decode_ms"] + rb2["decode_ms"],
                    "total_ms": ra["total_ms"] + rb2["total_ms"],
                    "logical_bytes": 0,
                }

                r_f1 = run_single_pass(model, f_ids, stop_ids, nl_id, arm_mode="base")
                r_f2 = run_single_pass(model, hb_ids, stop_ids, nl_id, arm_mode="base")
                pf = r_f1 if r_f1["mean_logprob"] >= r_f2["mean_logprob"] else r_f2
                rfull2 = {
                    "generated_ids": pf["generated_ids"],
                    "setup_ms": 0.0,
                    "first_token_ms": r_f1["first_token_ms"] + r_f2["first_token_ms"],
                    "decode_ms": r_f1["decode_ms"] + r_f2["decode_ms"],
                    "total_ms": r_f1["total_ms"] + r_f2["total_ms"],
                    "logical_bytes": 0,
                }

                for arm_name, r_arm in (
                    ("base", rb),
                    ("zero_fastweight", rz),
                    ("focal_fastweight", rf),
                    ("wrong_context_fastweight", rw),
                    ("random_fastweight", rr),
                    ("matched_compute_split2pass", rsplit),
                    ("matched_compute_full2pass", rfull2),
                ):
                    raw_txt = tok.decode(r_arm["generated_ids"], skip_special_tokens=True).strip().split("\n")[0].strip()
                    rows.append({
                        "id": t["id"],
                        "domain": t["domain"],
                        "arm": arm_name,
                        "input_tokens": len(t["f_ids"]),
                        "expected": t["expected"],
                        "output": raw_txt,
                        "correct": is_equivalent_output(raw_txt, t["expected"]),
                        "setup_ms": r_arm.get("setup_ms", 0.0),
                        "setup_ms_repeats": r_arm.get("setup_ms_repeats"),
                        "donor_setup_ms": r_arm.get("donor_setup_ms", 0.0),
                        "first_token_ms": r_arm["first_token_ms"],
                        "decode_ms": r_arm["decode_ms"],
                        "total_ms": r_arm["total_ms"],
                        "total_ms_repeats": r_arm.get("total_ms_repeats"),
                        "total_ms_std": r_arm.get("total_ms_std", 0.0),
                        "logical_bytes": r_arm["logical_bytes"],
                    })
                torch.mps.empty_cache()
            print(f"[v2-confirm] completed domain={dom}", flush=True)

    arm_names = [
        "base",
        "zero_fastweight",
        "focal_fastweight",
        "wrong_context_fastweight",
        "random_fastweight",
        "matched_compute_split2pass",
        "matched_compute_full2pass",
    ]
    base_rows = [r for r in rows if r["arm"] == "base"]
    base_mean_ms = statistics.mean(r["total_ms"] for r in base_rows)
    focal_map = {r["id"]: r for r in rows if r["arm"] == "focal_fastweight"}

    arms_summary = {}
    for a in arm_names:
        ar = [r for r in rows if r["arm"] == a]
        tots = [r["total_ms"] for r in ar]
        sets = [r["setup_ms"] for r in ar]
        by_d = {d: sum(1 for r in ar if r["domain"] == d and r["correct"]) for d in sorted(by_dom)}
        arms_summary[a] = {
            "correct": sum(1 for r in ar if r["correct"]),
            "total": len(ar),
            "accuracy": sum(1 for r in ar if r["correct"]) / len(ar),
            "by_domain": by_d,
            "mean_setup_ms": statistics.mean(sets),
            "p50_setup_ms": percentile(sets, 0.50),
            "p95_setup_ms": percentile(sets, 0.95),
            "setup_pct_of_base": 100.0 * statistics.mean(sets) / base_mean_ms,
            "mean_first_token_ms": statistics.mean(r["first_token_ms"] for r in ar),
            "mean_decode_ms": statistics.mean(r["decode_ms"] for r in ar),
            "mean_total_ms": statistics.mean(tots),
            "p50_total_ms": percentile(tots, 0.50),
            "p95_total_ms": percentile(tots, 0.95),
            "mean_within_task_repeat_std_ms": statistics.mean(r["total_ms_std"] for r in ar),
            "total_overhead_pct": 100.0 * (statistics.mean(tots) - base_mean_ms) / base_mean_ms,
            "mean_logical_bytes": statistics.mean(r["logical_bytes"] for r in ar),
        }

    paired = {}
    for ctrl in ("base", "wrong_context_fastweight", "random_fastweight", "matched_compute_split2pass", "matched_compute_full2pass"):
        cmap = {r["id"]: r for r in rows if r["arm"] == ctrl}
        w = sum(1 for tid, fr in focal_map.items() if fr["correct"] and not cmap[tid]["correct"])
        l = sum(1 for tid, fr in focal_map.items() if (not fr["correct"]) and cmap[tid]["correct"])
        paired[f"focal_vs_{ctrl}"] = {
            "focal_wins": w,
            "control_wins": l,
            "net_wins": w - l,
            "mcnemar_two_sided_p": exact_mcnemar_two_sided_p(w, l),
        }

    strongest_mc = (
        "matched_compute_full2pass"
        if arms_summary["matched_compute_full2pass"]["correct"] >= arms_summary["matched_compute_split2pass"]["correct"]
        else "matched_compute_split2pass"
    )
    mc_test = paired[f"focal_vs_{strongest_mc}"]
    b_test = paired["focal_vs_base"]
    wc_test = paired["focal_vs_wrong_context_fastweight"]
    rd_test = paired["focal_vs_random_fastweight"]
    f_sum = arms_summary["focal_fastweight"]

    gates = {
        "strongest_matched_compute_arm": strongest_mc,
        "beat_base_p_lt_005": b_test["net_wins"] > 0 and b_test["mcnemar_two_sided_p"] < 0.05,
        "beat_strongest_matched_compute_p_lt_005": mc_test["net_wins"] > 0 and mc_test["mcnemar_two_sided_p"] < 0.05,
        "beat_wrong_context_p_lt_001": wc_test["net_wins"] > 0 and wc_test["mcnemar_two_sided_p"] < 0.01,
        "beat_random_p_lt_001": rd_test["net_wins"] > 0 and rd_test["mcnemar_two_sided_p"] < 0.01,
        "setup_under_5pct_of_base": f_sum["setup_pct_of_base"] < 5.0,
        "faster_than_strongest_matched_compute": f_sum["mean_total_ms"] <= arms_summary[strongest_mc]["mean_total_ms"],
    }
    gates["all_pre_registered_criteria_met"] = all(
        v for k, v in gates.items() if k != "strongest_matched_compute_arm"
    )

    canary_after = float(model.lm_head.weight.detach().cpu().float().norm().item())
    receipt = {
        "schema": "gamma.reconfiguration.query_swiglu_fastweight_v2.confirmation/v1",
        "model_path": str(args.model_path),
        "model_provenance_note": "Qwen3-0.6B-NHS-786708b3 loaded via standard Qwen3ForCausalLM (ttt_proj weights unused); CPT backbone provenance explicitly disclosed.",
        "seed": args.seed,
        "latency_repeats": R,
        "code_sha256": hashes,
        "arms": arms_summary,
        "paired_tests": paired,
        "gate_evaluation": gates,
        "base_weights_unchanged": abs(canary_after - canary_before) == 0.0,
        "concurrent_gpu_processes_pre": pre_procs,
        "concurrent_gpu_processes_post": check_gpu_processes(),
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "rows": rows,
    }
    args.output_json.write_text(json.dumps(receipt, indent=2))
    print(f"[v2-confirm] DONE base={arms_summary['base']['correct']}/{len(tasks)} -> focal={f_sum['correct']}/{len(tasks)} | gates={json.dumps(gates)}", flush=True)


if __name__ == "__main__":
    main()
