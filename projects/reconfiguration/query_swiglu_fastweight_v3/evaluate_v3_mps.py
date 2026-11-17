"""Frozen v3 unseen confirmation + explanatory ablations + PyTorchEngine verification (`seed=990001`)."""
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
REPO_ROOT = THIS_DIR.parents[2]
V1_DIR = THIS_DIR.parent / "query_swiglu_fastweight_v1"
for d in (REPO_ROOT, THIS_DIR, V1_DIR):
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))

from gamma.engines.engine_factory import get_engine
from gamma.fastweight import (
    FastWeightAdapter,
    FastWeightSession,
    derive_fastweight,
    extract_query_features_for_donor,
    make_random_adapter,
    make_zero_adapter,
)
from score_receipts import exact_mcnemar_two_sided_p, is_equivalent_output
from tasks_v3 import build_v3_unseen_tasks


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
    return float(s[min(len(s) - 1, max(0, round(q * (len(s) - 1))))])


def run_single_pass_v3(
    model,
    tok,
    prompt_ids: torch.Tensor,
    stop_ids: set[int],
    nl_id: int,
    arm_mode: str = "base",
    c_len: int | None = None,
    context_text: str = "",
    query_line_text: str = "",
    donor_ad: FastWeightAdapter | None = None,
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
    session: FastWeightSession | None = None
    logical_b = 0
    decode_fn = lambda ids: tok.decode(ids, skip_special_tokens=True)
    encode_fn = lambda s: tok.encode(s, add_special_tokens=False)

    if arm_mode != "base":
        torch.mps.synchronize()
        ts = time.monotonic()
        use_key_gate = arm_mode != "ablation_no_key_gate"
        use_dyn_hop = arm_mode not in ("ablation_no_dynamic_hop", "ablation_no_key_gate", "zero", "random", "donor")
        use_loo_gate = arm_mode != "ablation_no_loo_gate"

        if arm_mode == "donor":
            assert donor_ad is not None
            xq_d = extract_query_features_for_donor(donor_ad, prompt_ids, nl_id, E_tok, hl_all)
            s_deltas = donor_ad.evaluate_query(xq_d, enable_key_gate=False)
            session = FastWeightSession(donor_ad, s_deltas, prompt_ids.device, enable_dynamic_hop=False)
            logical_b = donor_ad.logical_bytes
        else:
            assert c_len is not None
            ad, xq = derive_fastweight(
                prompt_ids, c_len, nl_id, E_tok, hl_all, W_lm,
                context_text=context_text,
                query_line_text=query_line_text,
                enable_key_gate=use_key_gate,
                enable_loo_nll_gate=use_loo_gate,
            )
            if arm_mode == "zero":
                ad = make_zero_adapter(ad)
            elif arm_mode == "random":
                ad = make_random_adapter(ad, seed=rand_seed)
            s_deltas = ad.evaluate_query(
                xq,
                enable_key_gate=use_key_gate if arm_mode != "random" else False,
                encode_fn=encode_fn if (use_key_gate and arm_mode not in ("zero", "random")) else None,
            )
            session = FastWeightSession(ad, s_deltas, prompt_ids.device, enable_dynamic_hop=use_dyn_hop)
            logical_b = ad.logical_bytes
        torch.mps.synchronize()
        setup_s = time.monotonic() - ts

    def logits_at(cur_hl_bf16: torch.Tensor, step_k: int) -> torch.Tensor:
        lf = model.lm_head(cur_hl_bf16.unsqueeze(0)).squeeze(0).float()
        if session is not None:
            lf = session.apply_to_logits(lf, step_k)
        return lf

    l0_f = logits_at(hl_all[-1], 0)
    first_sample = l0_f[:64].detach().cpu()
    nid = int(l0_f.argmax(dim=-1).item())
    sum_lp = float((l0_f[nid] - torch.logsumexp(l0_f, dim=-1)).item())
    nxt = torch.tensor([[nid]], device=prompt_ids.device, dtype=torch.long)
    gen = [nid]
    if session is not None:
        session.on_token_sampled(nid, 1, decode_fn=decode_fn, encode_fn=encode_fn)
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
        if session is not None:
            session.on_token_sampled(nid, step_k, decode_fn=decode_fn, encode_fn=encode_fn)

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
        "mode": session.adapter.mode if session is not None else "none",
        "dynamic_hops": session.dynamic_hops_triggered if session is not None else 0,
    }


def derive_donor_v3(model, donor_ids: torch.Tensor, donor_c_len: int, nl_id: int) -> tuple[FastWeightAdapter, float]:
    torch.mps.synchronize()
    t0 = time.monotonic()
    out = model.model(input_ids=donor_ids, use_cache=False, return_dict=True)
    ad, _ = derive_fastweight(
        donor_ids, donor_c_len, nl_id, model.model.embed_tokens.weight, out.last_hidden_state[0], model.lm_head.weight,
        enable_key_gate=False,
    )
    torch.mps.synchronize()
    return ad, (time.monotonic() - t0) * 1000.0


def verify_pytorch_engine_integration(model_path: Path, sample_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify end-to-end `get_engine('pytorch', ..., {'fastweight': True})` runtime parity."""
    eng = get_engine("pytorch", str(model_path), {"fastweight": True, "mode": "benchmark"})
    eng.load()
    nl_id = eng.tokenizer.encode("\n", add_special_tokens=False)[-1]
    stop_ids = {eng.tokenizer.eos_token_id, nl_id}

    correct = 0
    modes = []
    for t in sample_tasks:
        eng.reset_kv_cache()
        inp_ids, attn_mask = eng.encode(t["prompt"], add_special_tokens=False)
        res = eng.predict_next(inp_ids, attn_mask, temperature=0.0, top_k=1, top_p=1.0)
        gen = [int(res["next_token_id"])]
        while len(gen) < 16 and gen[-1] not in stop_ids:
            nxt = torch.tensor([[gen[-1]]], device=inp_ids.device, dtype=torch.long)
            res = eng.predict_next(nxt, None, temperature=0.0, top_k=1, top_p=1.0)
            gen.append(int(res["next_token_id"]))
        txt = eng.decode(gen, skip_special_tokens=True).strip().split("\n")[0].strip()
        if is_equivalent_output(txt, t["expected"]):
            correct += 1
        modes.append(eng.fastweight_stats["mode"] if eng.fastweight_stats else "none")
    del eng
    torch.mps.empty_cache()
    return {"sample_count": len(sample_tasks), "correct": correct, "observed_modes": modes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=990001)
    ap.add_argument("--count-per-domain", type=int, default=16)
    ap.add_argument("--latency-repeats", type=int, default=3)
    args = ap.parse_args()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    pre_procs = check_gpu_processes()

    hashes = {
        "gamma_fastweight_adapter.py": file_sha256(REPO_ROOT / "gamma" / "fastweight" / "adapter.py"),
        "tasks_v3.py": file_sha256(THIS_DIR / "tasks_v3.py"),
        "score_receipts.py": file_sha256(V1_DIR / "score_receipts.py"),
        "evaluate_v3_mps.py": file_sha256(THIS_DIR / "evaluate_v3_mps.py"),
    }
    args.output_json.with_suffix(".protocol.json").write_text(json.dumps({
        "schema": "gamma.reconfiguration.query_swiglu_fastweight_v3.protocol/v1",
        "seed": args.seed,
        "count_per_domain": args.count_per_domain,
        "latency_repeats_per_task": args.latency_repeats,
        "code_sha256": hashes,
        "pre_registered_success_criteria": {
            "focal_vs_base_mcnemar_p_lt": 0.05,
            "focal_vs_strongest_matched_compute_mcnemar_p_lt": 0.05,
            "focal_vs_wrong_context_mcnemar_p_lt": 0.01,
            "focal_vs_random_mcnemar_p_lt": 0.01,
            "mean_setup_pct_of_base_lt": 5.0,
        },
    }, indent=2))

    tasks = build_v3_unseen_tasks(seed=args.seed, count_per_domain=args.count_per_domain)
    by_dom: dict[str, list[dict[str, Any]]] = {}
    for t in tasks:
        by_dom.setdefault(t["domain"], []).append(t)

    # First verify Gamma's `PyTorchEngine(fastweight=True)` on 1 sample per domain
    engine_smoke = verify_pytorch_engine_integration(args.model_path, [d_list[0] for d_list in by_dom.values()])
    print(f"[v3-confirm] PyTorchEngine smoke check: {json.dumps(engine_smoke)}", flush=True)

    tok = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False, fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path, local_files_only=True, trust_remote_code=False, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).to("mps").eval()
    nl_id = tok.encode("\n", add_special_tokens=False)[-1]
    stop_ids = {tok.eos_token_id, nl_id}
    canary_before = float(model.lm_head.weight.detach().cpu().float().norm().item())

    for t in tasks:
        c_ids = tok.encode(t["context_text"], add_special_tokens=False)
        f_ids = tok.encode(t["prompt"], add_special_tokens=False)
        assert f_ids[: len(c_ids)] == c_ids
        t["c_ids"] = c_ids
        t["f_ids"] = f_ids
        t["ha_ids"] = tok.encode(t["half_a_prompt"], add_special_tokens=False)
        t["hb_ids"] = tok.encode(t["half_b_prompt"], add_special_tokens=False)

    rows = []
    R = int(args.latency_repeats)
    with torch.inference_mode():
        warm = torch.tensor([[nl_id] * 24], device="mps", dtype=torch.long)
        _ = run_single_pass_v3(model, tok, warm, stop_ids, nl_id, arm_mode="base", max_new=2)

        for dom, d_tasks in by_dom.items():
            n_d = len(d_tasks)
            for i, t in enumerate(d_tasks):
                donor_t = d_tasks[(i + 1) % n_d]
                f_ids = torch.tensor([t["f_ids"]], device="mps", dtype=torch.long)
                c_len = len(t["c_ids"])
                ctx_txt = t["context_text"]
                qry_txt = t["query_text"]

                b_runs = []
                f_runs = []
                for _ in range(R):
                    b_runs.append(run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="base"))
                    f_runs.append(run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="focal", c_len=c_len, context_text=ctx_txt, query_line_text=qry_txt))

                def agg_repeats(runs: list[dict[str, Any]]) -> dict[str, Any]:
                    s_ms = [x["setup_ms"] for x in runs]
                    tt_ms = [x["total_ms"] for x in runs]
                    agree = sum(1 for x in runs if x["generated_ids"] == runs[0]["generated_ids"]) / len(runs)
                    return {
                        "generated_ids": runs[0]["generated_ids"],
                        "repeat_exact_match": agree,
                        "first_logits_sample": runs[0]["first_logits_sample"],
                        "setup_ms": statistics.mean(s_ms),
                        "setup_ms_repeats": s_ms,
                        "first_token_ms": statistics.mean(x["first_token_ms"] for x in runs),
                        "decode_ms": statistics.mean(x["decode_ms"] for x in runs),
                        "total_ms": statistics.mean(tt_ms),
                        "total_ms_repeats": tt_ms,
                        "total_ms_std": statistics.pstdev(tt_ms),
                        "logical_bytes": runs[0]["logical_bytes"],
                        "mode": runs[0]["mode"],
                        "dynamic_hops": runs[0]["dynamic_hops"],
                    }

                rb = agg_repeats(b_runs)
                rf = agg_repeats(f_runs)

                rz = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="zero", c_len=c_len, context_text=ctx_txt, query_line_text=qry_txt)
                assert float((b_runs[0]["first_logits_sample"] - rz["first_logits_sample"]).abs().max().item()) < 0.05

                d_ids = torch.tensor([donor_t["f_ids"]], device="mps", dtype=torch.long)
                donor_ad, donor_ms = derive_donor_v3(model, d_ids, len(donor_t["c_ids"]), nl_id)
                rw = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="donor", donor_ad=donor_ad)
                rw["donor_setup_ms"] = donor_ms
                rw["total_ms"] += donor_ms

                rr = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="random", c_len=c_len, rand_seed=996000 + i)

                # Explanatory ablations isolating the 3 causal mechanisms of v3
                rab_nokey = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="ablation_no_key_gate", c_len=c_len, context_text=ctx_txt, query_line_text=qry_txt)
                rab_nohop = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="ablation_no_dynamic_hop", c_len=c_len, context_text=ctx_txt, query_line_text=qry_txt)
                rab_noloo = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="ablation_no_loo_gate", c_len=c_len, context_text=ctx_txt, query_line_text=qry_txt)

                ha_ids = torch.tensor([t["ha_ids"]], device="mps", dtype=torch.long)
                hb_ids = torch.tensor([t["hb_ids"]], device="mps", dtype=torch.long)
                ra = run_single_pass_v3(model, tok, ha_ids, stop_ids, nl_id, arm_mode="base")
                rb2 = run_single_pass_v3(model, tok, hb_ids, stop_ids, nl_id, arm_mode="base")
                ps = ra if ra["mean_logprob"] >= rb2["mean_logprob"] else rb2
                rsplit = {
                    "generated_ids": ps["generated_ids"],
                    "setup_ms": 0.0,
                    "first_token_ms": ra["first_token_ms"] + rb2["first_token_ms"],
                    "decode_ms": ra["decode_ms"] + rb2["decode_ms"],
                    "total_ms": ra["total_ms"] + rb2["total_ms"],
                    "logical_bytes": 0,
                }

                r_f1 = run_single_pass_v3(model, tok, f_ids, stop_ids, nl_id, arm_mode="base")
                r_f2 = run_single_pass_v3(model, tok, hb_ids, stop_ids, nl_id, arm_mode="base")
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
                    ("ablation_no_key_gate", rab_nokey),
                    ("ablation_no_dynamic_hop", rab_nohop),
                    ("ablation_no_loo_gate", rab_noloo),
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
                        "mode": r_arm.get("mode", "none"),
                        "dynamic_hops": r_arm.get("dynamic_hops", 0),
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
            print(f"[v3-confirm] completed domain={dom}", flush=True)

    arm_names = [
        "base",
        "zero_fastweight",
        "focal_fastweight",
        "ablation_no_key_gate",
        "ablation_no_dynamic_hop",
        "ablation_no_loo_gate",
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
            "dynamic_hops_triggered": sum(r["dynamic_hops"] for r in ar),
        }

    paired = {}
    for ctrl in (
        "base",
        "ablation_no_key_gate",
        "ablation_no_dynamic_hop",
        "ablation_no_loo_gate",
        "wrong_context_fastweight",
        "random_fastweight",
        "matched_compute_split2pass",
        "matched_compute_full2pass",
    ):
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
        "schema": "gamma.reconfiguration.query_swiglu_fastweight_v3.confirmation/v1",
        "model_path": str(args.model_path),
        "model_provenance_note": "Qwen3-0.6B-NHS-786708b3 loaded via standard Qwen3ForCausalLM (ttt_proj weights unused); CPT backbone provenance explicitly disclosed.",
        "seed": args.seed,
        "latency_repeats": R,
        "code_sha256": hashes,
        "pytorch_engine_smoke": engine_smoke,
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
    print(f"[v3-confirm] DONE base={arms_summary['base']['correct']}/{len(tasks)} -> focal={f_sum['correct']}/{len(tasks)} | setup={f_sum['setup_pct_of_base']:.2f}% | gates={json.dumps(gates)}", flush=True)


if __name__ == "__main__":
    main()
