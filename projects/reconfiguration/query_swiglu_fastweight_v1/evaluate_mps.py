"""Stage 1 candidate selection and Stage 2 sealed confirmation on PyTorch MPS.

Protocol:
1. `--stage stage1`: Evaluates `base` and all 5 frozen candidates (`C1..C5`) on fresh `dev_families`
   `seed=810001` (`12` tasks/domain = `48` tasks). Selects the single winning candidate maximizing:
       selection_score = accuracy - 0.25 * max(0.0, total_overhead_ratio - 0.05)
   (breaking exact ties toward zero-hook portable candidates `C4/C5`) and writes a sealed Stage 1 receipt.
2. `--stage stage2`: Loads the sealed Stage 1 winner from `--stage1-receipt` without retuning and evaluates
   128 fresh tasks (`64` fresh `dev_families` on `seed=920001` + `64` brand-new unseen `holdout_families`
   on `seed=930001`) across all 7 arms:
   - `base`
   - `zero_fastweight`
   - `focal_fastweight`
   - `wrong_context_fastweight` (same-domain donor `(i + 1) % n_dom`, charging donor setup + own run)
   - `random_fastweight` (Frobenius-norm-matched Gaussian fast weights)
   - `matched_compute_split2pass` (2-pass unmodified base over `half_a` + `half_b`, confidence-selected)
   - `matched_compute_full2pass` (2-pass unmodified base over full prompt + focused tail prompt, confidence-selected;
     spends >= `focal_fastweight` compute while retaining full-context visibility)
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import comb
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from tasks import build_dev_family_tasks, build_holdout_family_tasks
from transforms import (
    CANDIDATE_NAMES,
    FastWeightAdapter,
    derive_fastweight_From_states,
    extract_query_features_for_donor,
    make_random_adapter,
    make_zero_adapter,
)


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def normalize_line(text: str) -> str:
    first = (text or "").strip().split("\n")[0].strip().rstrip("`.,;")
    return " ".join(first.split())


def exact_mcnemar_two_sided_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, j) for j in range(k + 1)) / float(2 ** n)
    return min(1.0, 2.0 * tail)


def check_gpu_processes() -> list[str]:
    out = subprocess.check_output(["ps", "-Ao", "pid,pcpu,pmem,etime,command"], text=True)
    hits = []
    my_pid = os.getpid()
    for ln in out.splitlines():
        if any(k in ln for k in ("flash-native", "native-whole-service", "evaluate_doppler")) and str(my_pid) not in ln:
            hits.append(ln.strip())
    return hits


def rss_bytes() -> int:
    # ru_maxrss on macOS is in bytes
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def prefill_and_decode(
    model,
    prompt_ids: torch.Tensor,
    stop_ids: set[int],
    newline_id: int,
    max_new: int = 16,
    candidate: str | None = None,
    c_len: int | None = None,
    arm_mode: str = "base",                # 'base' | 'focal' | 'zero' | 'random' | 'donor'
    donor_adapter: FastWeightAdapter | None = None,
    rand_seed: int = 0,
) -> dict[str, Any]:
    """Execute ONE single prefill pass + greedy multi-token decode, measuring exact phase latencies."""
    uses_hooks = False
    if candidate is not None and arm_mode != "base":
        uses_hooks = candidate in ("C1_linear_window_ridge", "C2_isotropic_swiglu", "C3_snr_swiglu_logitres")

    n_layers = len(model.model.layers)
    cap: dict[str, torch.Tensor] = {}
    h1 = h2 = None
    if uses_hooks:
        def hk(k: str):
            def fn(_m, _i, o):
                cap[k] = (o[0] if isinstance(o, tuple) else o).detach()
            return fn
        h1 = model.model.layers[1].register_forward_hook(hk("e"))
        h2 = model.model.layers[n_layers // 2].register_forward_hook(hk("m"))

    try:
        torch.mps.synchronize()
        t0 = time.monotonic()
        out = model.model(input_ids=prompt_ids, use_cache=True, return_dict=True)
        hl_all = out.last_hidden_state[0]
        cache = out.past_key_values
        if h1 is not None:
            h1.remove(); h1 = None
        if h2 is not None:
            h2.remove(); h2 = None

        setup_s = 0.0
        step_deltas: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
        derived_adapter: FastWeightAdapter | None = None
        logical_b = 0

        W_lm = model.lm_head.weight
        E_tok = model.model.embed_tokens.weight

        if arm_mode != "base" and candidate is not None:
            torch.mps.synchronize()
            ts = time.monotonic()
            he_b = cap.get("e", [None])[0] if "e" in cap else None
            hm_b = cap.get("m", [None])[0] if "m" in cap else None

            if arm_mode == "donor":
                assert donor_adapter is not None
                xq_d = extract_query_features_for_donor(
                    donor_adapter, prompt_ids, newline_id, E_tok, hl_all, he_b, hm_b
                )
                if xq_d is not None:
                    step_deltas = donor_adapter.evaluate_query(xq_d)
                logical_b = donor_adapter.logical_bytes
                derived_adapter = donor_adapter
            else:
                assert c_len is not None
                ad, xq = derive_fastweight_From_states(
                    candidate=candidate,
                    prompt_ids=prompt_ids,
                    c_len=c_len,
                    newline_id=newline_id,
                    E_tok_bf16=E_tok,
                    h_last_bf16=hl_all,
                    W_lm_bf16=W_lm,
                    h_early_bf16=he_b,
                    h_mid_bf16=hm_b,
                )
                if arm_mode == "zero":
                    ad = make_zero_adapter(ad)
                elif arm_mode == "random":
                    ad = make_random_adapter(ad, seed=rand_seed)
                derived_adapter = ad
                logical_b = ad.logical_bytes
                if xq is not None:
                    step_deltas = ad.evaluate_query(xq)

            torch.mps.synchronize()
            setup_s = time.monotonic() - ts

        def logits_at_step(cur_hl_bf16: torch.Tensor, step_k: int) -> torch.Tensor:
            l_step_f = model.lm_head(cur_hl_bf16.unsqueeze(0)).squeeze(0).float()
            if step_k in step_deltas:
                u_t, dv = step_deltas[step_k]
                if dv.abs().max().item() > 0.0:
                    l_step_f = l_step_f.clone()
                    l_step_f.index_add_(0, u_t, dv.float())
            return l_step_f

        l0_f = logits_at_step(hl_all[-1], 0)
        first_sample = l0_f[:64].detach().cpu()
        nxt_id = int(l0_f.argmax(dim=-1).item())
        sum_lp = float((l0_f[nxt_id] - torch.logsumexp(l0_f, dim=-1)).item())
        nxt = torch.tensor([[nxt_id]], device=prompt_ids.device, dtype=torch.long)
        gen = [nxt_id]
        torch.mps.synchronize()
        t_first = time.monotonic()

        step_k = 1
        while len(gen) < max_new and gen[-1] not in stop_ids:
            r_s = model.model(input_ids=nxt, past_key_values=cache, use_cache=True, return_dict=True)
            cache = r_s.past_key_values
            lk_f = logits_at_step(r_s.last_hidden_state[0, -1], step_k)
            nid = int(lk_f.argmax(dim=-1).item())
            sum_lp += float((lk_f[nid] - torch.logsumexp(lk_f, dim=-1)).item())
            nxt = torch.tensor([[nid]], device=prompt_ids.device, dtype=torch.long)
            gen.append(nid)
            step_k += 1

        torch.mps.synchronize()
        t_end = time.monotonic()
    finally:
        if h1 is not None:
            h1.remove()
        if h2 is not None:
            h2.remove()

    return {
        "generated_ids": gen,
        "mean_logprob": sum_lp / max(1, len(gen)),
        "first_logits_sample": first_sample,
        "setup_ms": setup_s * 1000.0,
        "first_token_ms": (t_first - t0) * 1000.0,
        "decode_ms": (t_end - t_first) * 1000.0,
        "total_ms": (t_end - t0) * 1000.0,
        "logical_bytes": logical_b,
        "adapter": derived_adapter,
    }


def derive_donor_only(
    model,
    donor_prompt_ids: torch.Tensor,
    donor_c_len: int,
    newline_id: int,
    candidate: str,
) -> tuple[FastWeightAdapter, float]:
    """Run donor context prefill + fast-weight derivation and return (adapter, donor_setup_ms) for full cost accounting."""
    uses_hooks = candidate in ("C1_linear_window_ridge", "C2_isotropic_swiglu", "C3_snr_swiglu_logitres")
    n_layers = len(model.model.layers)
    cap: dict[str, torch.Tensor] = {}
    h1 = h2 = None
    if uses_hooks:
        def hk(k: str):
            def fn(_m, _i, o):
                cap[k] = (o[0] if isinstance(o, tuple) else o).detach()
            return fn
        h1 = model.model.layers[1].register_forward_hook(hk("e"))
        h2 = model.model.layers[n_layers // 2].register_forward_hook(hk("m"))
    try:
        torch.mps.synchronize()
        t0 = time.monotonic()
        out = model.model(input_ids=donor_prompt_ids, use_cache=False, return_dict=True)
        hl_all = out.last_hidden_state[0]
        if h1 is not None:
            h1.remove(); h1 = None
        if h2 is not None:
            h2.remove(); h2 = None
        ad, _ = derive_fastweight_From_states(
            candidate=candidate,
            prompt_ids=donor_prompt_ids,
            c_len=donor_c_len,
            newline_id=newline_id,
            E_tok_bf16=model.model.embed_tokens.weight,
            h_last_bf16=hl_all,
            W_lm_bf16=model.lm_head.weight,
            h_early_bf16=cap["e"][0] if "e" in cap else None,
            h_mid_bf16=cap["m"][0] if "m" in cap else None,
        )
        torch.mps.synchronize()
        elapsed_ms = (time.monotonic() - t0) * 1000.0
    finally:
        if h1 is not None:
            h1.remove()
        if h2 is not None:
            h2.remove()
    return ad, elapsed_ms


def prepare_tokenized_tasks(tasks: list[dict[str, Any]], tok) -> list[dict[str, Any]]:
    for t in tasks:
        c_ids = tok.encode(t["context_text"], add_special_tokens=False)
        f_ids = tok.encode(t["prompt"], add_special_tokens=False)
        assert f_ids[: len(c_ids)] == c_ids, f"BPE boundary mismatch on {t['id']}"
        t["c_ids"] = c_ids
        t["f_ids"] = f_ids
        t["ha_ids"] = tok.encode(t["half_a_prompt"], add_special_tokens=False)
        t["hb_ids"] = tok.encode(t["half_b_prompt"], add_special_tokens=False)
    return tasks


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("stage1", "stage2"), required=True)
    ap.add_argument("--model-path", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--stage1-receipt", type=Path, default=None)
    args = ap.parse_args()

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    pre_procs = check_gpu_processes()

    tok = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False, fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    ).to("mps").eval()

    nl_id = tok.encode("\n", add_special_tokens=False)[0]
    stop_ids = {tok.eos_token_id, nl_id}
    canary_param = model.lm_head.weight
    canary_norm_before = float(canary_param.detach().cpu().float().norm().item())

    transforms_sha = file_sha256(THIS_DIR / "transforms.py")
    tasks_sha = file_sha256(THIS_DIR / "tasks.py")

    with torch.inference_mode():
        # Warmup Metal shaders before timed loops
        warm = torch.tensor([[nl_id] * 24], device="mps", dtype=torch.long)
        _ = prefill_and_decode(model, warm, stop_ids, nl_id, max_new=2, arm_mode="base")

        if args.stage == "stage1":
            tasks = prepare_tokenized_tasks(build_dev_family_tasks(seed=810001, count_per_domain=12), tok)
            proto_path = args.output_json.with_suffix(".protocol.json")
            proto_path.write_text(json.dumps({
                "stage": "stage1_selection",
                "seed": 810001,
                "count_per_domain": 12,
                "candidates": list(CANDIDATE_NAMES),
                "selection_rule": "accuracy - 0.25 * max(0.0, total_overhead_ratio - 0.05)",
                "transforms_sha256": transforms_sha,
                "tasks_sha256": tasks_sha,
            }, indent=2))

            arms = ["base"] + list(CANDIDATE_NAMES)
            rows = []
            for t in tasks:
                f_ids = torch.tensor([t["f_ids"]], device="mps", dtype=torch.long)
                c_len = len(t["c_ids"])
                for arm in arms:
                    res = prefill_and_decode(
                        model,
                        f_ids,
                        stop_ids,
                        nl_id,
                        max_new=16,
                        candidate=None if arm == "base" else arm,
                        c_len=None if arm == "base" else c_len,
                        arm_mode="base" if arm == "base" else "focal",
                    )
                    txt = tok.decode(res["generated_ids"], skip_special_tokens=True)
                    ok = normalize_line(txt) == t["expected"]
                    rows.append({
                        "id": t["id"],
                        "domain": t["domain"],
                        "arm": arm,
                        "expected": t["expected"],
                        "output": normalize_line(txt),
                        "correct": ok,
                        "setup_ms": res["setup_ms"],
                        "first_token_ms": res["first_token_ms"],
                        "decode_ms": res["decode_ms"],
                        "total_ms": res["total_ms"],
                        "logical_bytes": res["logical_bytes"],
                    })
                torch.mps.empty_cache()

            base_rows = [r for r in rows if r["arm"] == "base"]
            base_mean_ms = sum(r["total_ms"] for r in base_rows) / len(base_rows)
            base_acc = sum(1 for r in base_rows if r["correct"]) / len(base_rows)

            cand_summaries = {}
            best_cand = None
            best_key = (-1e9, -1, -1e9)
            for cand in CANDIDATE_NAMES:
                cr = [r for r in rows if r["arm"] == cand]
                acc = sum(1 for r in cr if r["correct"]) / len(cr)
                mean_tot = sum(r["total_ms"] for r in cr) / len(cr)
                mean_set = sum(r["setup_ms"] for r in cr) / len(cr)
                ovh = (mean_tot - base_mean_ms) / max(base_mean_ms, 1e-6)
                sel_score = acc - 0.25 * max(0.0, ovh - 0.05)
                is_portable = 1 if cand.startswith("C4_") or cand.startswith("C5_") else 0
                by_dom = {
                    d: sum(1 for r in cr if r["domain"] == d and r["correct"])
                    for d in sorted({r["domain"] for r in cr})
                }
                cand_summaries[cand] = {
                    "correct": sum(1 for r in cr if r["correct"]),
                    "total": len(cr),
                    "accuracy": acc,
                    "by_domain": by_dom,
                    "mean_setup_ms": mean_set,
                    "setup_pct_of_base": 100.0 * mean_set / base_mean_ms,
                    "mean_total_ms": mean_tot,
                    "total_overhead_pct": 100.0 * ovh,
                    "selection_score": sel_score,
                    "portable_zero_hook": bool(is_portable),
                }
                key = (round(sel_score, 6), is_portable, -ovh)
                if key > best_key:
                    best_key = key
                    best_cand = cand

            canary_norm_after = float(canary_param.detach().cpu().float().norm().item())
            receipt = {
                "schema": "gamma.reconfiguration.query_swiglu_fastweight.stage1/v1",
                "model_path": str(args.model_path),
                "model_provenance_note": "Qwen3-0.6B-NHS-786708b3 loaded via standard Qwen3ForCausalLM (ttt_proj weights unused); CPT backbone provenance explicitly disclosed.",
                "seed": 810001,
                "transforms_sha256": transforms_sha,
                "tasks_sha256": tasks_sha,
                "base_summary": {
                    "correct": sum(1 for r in base_rows if r["correct"]),
                    "total": len(base_rows),
                    "accuracy": base_acc,
                    "by_domain": {
                        d: sum(1 for r in base_rows if r["domain"] == d and r["correct"])
                        for d in sorted({r["domain"] for r in base_rows})
                    },
                    "mean_total_ms": base_mean_ms,
                },
                "candidate_summaries": cand_summaries,
                "selected_winner": best_cand,
                "base_weights_unchanged": abs(canary_norm_after - canary_norm_before) == 0.0,
                "concurrent_gpu_processes_pre": pre_procs,
                "concurrent_gpu_processes_post": check_gpu_processes(),
                "peak_rss_bytes": rss_bytes(),
                "rows": rows,
            }
            args.output_json.write_text(json.dumps(receipt, indent=2))
            print(f"[stage1] base={receipt['base_summary']['correct']}/{len(base_rows)} ({base_mean_ms:.1f}ms) -> winner={best_cand}: {json.dumps(cand_summaries[best_cand])}")
            return

        # Stage 2 sealed confirmation
        assert args.stage1_receipt is not None and args.stage1_receipt.exists(), "--stage1-receipt required for stage2"
        s1_data = json.loads(args.stage1_receipt.read_text())
        assert s1_data["transforms_sha256"] == transforms_sha, "transforms.py changed after Stage 1 freeze!"
        winner = s1_data["selected_winner"]

        dev_tasks = prepare_tokenized_tasks(build_dev_family_tasks(seed=920001, count_per_domain=16), tok)
        hold_tasks = prepare_tokenized_tasks(build_holdout_family_tasks(seed=930001, count_per_domain=16), tok)
        all_tasks = dev_tasks + hold_tasks

        proto_path = args.output_json.with_suffix(".protocol.json")
        proto_path.write_text(json.dumps({
            "stage": "stage2_sealed_confirmation",
            "selected_winner": winner,
            "stage1_receipt_sha256": file_sha256(args.stage1_receipt),
            "transforms_sha256": transforms_sha,
            "tasks_sha256": tasks_sha,
            "dev_seed": 920001,
            "holdout_seed": 930001,
            "total_tasks": len(all_tasks),
        }, indent=2))

        # Group tasks by domain so wrong_context uses same-domain next-instance donor!
        by_dom_tasks: dict[str, list[dict[str, Any]]] = {}
        for t in all_tasks:
            by_dom_tasks.setdefault(t["domain"], []).append(t)

        rows = []
        for dom, d_tasks in by_dom_tasks.items():
            n_d = len(d_tasks)
            for i, t in enumerate(d_tasks):
                donor_t = d_tasks[(i + 1) % n_d]
                f_ids = torch.tensor([t["f_ids"]], device="mps", dtype=torch.long)
                c_len = len(t["c_ids"])

                # 1. base
                rb = prefill_and_decode(model, f_ids, stop_ids, nl_id, arm_mode="base")
                # 2. zero_fastweight
                rz = prefill_and_decode(model, f_ids, stop_ids, nl_id, candidate=winner, c_len=c_len, arm_mode="zero")
                zero_diff = float((rb["first_logits_sample"] - rz["first_logits_sample"]).abs().max().item())
                assert zero_diff == 0.0, f"Zero control altered logits ({zero_diff}) on {t['id']}"

                # 3. focal_fastweight
                rf = prefill_and_decode(model, f_ids, stop_ids, nl_id, candidate=winner, c_len=c_len, arm_mode="focal")

                # 4. wrong_context_fastweight (charges donor prefill+derivation + target inference!)
                d_ids = torch.tensor([donor_t["f_ids"]], device="mps", dtype=torch.long)
                donor_ad, donor_ms = derive_donor_only(model, d_ids, len(donor_t["c_ids"]), nl_id, winner)
                rw = prefill_and_decode(
                    model, f_ids, stop_ids, nl_id, candidate=winner, c_len=c_len, arm_mode="donor", donor_adapter=donor_ad
                )
                rw["donor_setup_ms"] = donor_ms
                rw["total_ms"] = rw["total_ms"] + donor_ms

                # 5. random_fastweight
                rr = prefill_and_decode(
                    model, f_ids, stop_ids, nl_id, candidate=winner, c_len=c_len, arm_mode="random", rand_seed=900000 + i
                )

                # 6. matched_compute_split2pass (half_a + half_b unmodified base, confidence-selected)
                ha_ids = torch.tensor([t["ha_ids"]], device="mps", dtype=torch.long)
                hb_ids = torch.tensor([t["hb_ids"]], device="mps", dtype=torch.long)
                ra = prefill_and_decode(model, ha_ids, stop_ids, nl_id, arm_mode="base")
                rb2 = prefill_and_decode(model, hb_ids, stop_ids, nl_id, arm_mode="base")
                pick_s = ra if ra["mean_logprob"] >= rb2["mean_logprob"] else rb2
                rsplit = {
                    "generated_ids": pick_s["generated_ids"],
                    "setup_ms": 0.0,
                    "first_token_ms": ra["first_token_ms"] + rb2["first_token_ms"],
                    "decode_ms": ra["decode_ms"] + rb2["decode_ms"],
                    "total_ms": ra["total_ms"] + rb2["total_ms"],
                    "logical_bytes": 0,
                }

                # 7. matched_compute_full2pass (full prompt + half_b prompt unmodified base, confidence-selected; >= focal compute!)
                rb_full = prefill_and_decode(model, f_ids, stop_ids, nl_id, arm_mode="base")
                rb_tail = prefill_and_decode(model, hb_ids, stop_ids, nl_id, arm_mode="base")
                pick_f = rb_full if rb_full["mean_logprob"] >= rb_tail["mean_logprob"] else rb_tail
                rfull2 = {
                    "generated_ids": pick_f["generated_ids"],
                    "setup_ms": 0.0,
                    "first_token_ms": rb_full["first_token_ms"] + rb_tail["first_token_ms"],
                    "decode_ms": rb_full["decode_ms"] + rb_tail["decode_ms"],
                    "total_ms": rb_full["total_ms"] + rb_tail["total_ms"],
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
                    txt = normalize_line(tok.decode(r_arm["generated_ids"], skip_special_tokens=True))
                    rows.append({
                        "id": t["id"],
                        "group": t["group"],
                        "domain": t["domain"],
                        "arm": arm_name,
                        "input_tokens": len(t["f_ids"]),
                        "expected": t["expected"],
                        "output": txt,
                        "correct": txt == t["expected"],
                        "setup_ms": r_arm.get("setup_ms", 0.0),
                        "donor_setup_ms": r_arm.get("donor_setup_ms", 0.0),
                        "first_token_ms": r_arm["first_token_ms"],
                        "decode_ms": r_arm["decode_ms"],
                        "total_ms": r_arm["total_ms"],
                        "logical_bytes": r_arm["logical_bytes"],
                    })
                torch.mps.empty_cache()
            print(f"[stage2] completed domain={dom}", flush=True)

        def summarize_subset(sub_rows: list[dict[str, Any]]) -> dict[str, Any]:
            arm_names = [
                "base",
                "zero_fastweight",
                "focal_fastweight",
                "wrong_context_fastweight",
                "random_fastweight",
                "matched_compute_split2pass",
                "matched_compute_full2pass",
            ]
            by_arm = {}
            base_map = {r["id"]: r for r in sub_rows if r["arm"] == "base"}
            focal_map = {r["id"]: r for r in sub_rows if r["arm"] == "focal_fastweight"}
            base_ms = sum(r["total_ms"] for r in base_map.values()) / len(base_map)

            for a in arm_names:
                ar = [r for r in sub_rows if r["arm"] == a]
                c_cnt = sum(1 for r in ar if r["correct"])
                m_tot = sum(r["total_ms"] for r in ar) / len(ar)
                m_set = sum(r["setup_ms"] for r in ar) / len(ar)
                m_ft = sum(r["first_token_ms"] for r in ar) / len(ar)
                m_dec = sum(r["decode_ms"] for r in ar) / len(ar)
                m_bytes = sum(r["logical_bytes"] for r in ar) / len(ar)
                by_dom = {
                    d: sum(1 for r in ar if r["domain"] == d and r["correct"])
                    for d in sorted({r["domain"] for r in ar})
                }
                by_arm[a] = {
                    "correct": c_cnt,
                    "total": len(ar),
                    "accuracy": c_cnt / len(ar),
                    "by_domain": by_dom,
                    "mean_setup_ms": m_set,
                    "setup_pct_of_base": 100.0 * m_set / base_ms,
                    "mean_first_token_ms": m_ft,
                    "mean_decode_ms": m_dec,
                    "mean_total_ms": m_tot,
                    "total_overhead_pct": 100.0 * (m_tot - base_ms) / base_ms,
                    "mean_logical_bytes": m_bytes,
                }

            paired = {}
            for ctrl in (
                "base",
                "wrong_context_fastweight",
                "random_fastweight",
                "matched_compute_split2pass",
                "matched_compute_full2pass",
            ):
                cmap = {r["id"]: r for r in sub_rows if r["arm"] == ctrl}
                wins = sum(1 for tid, fr in focal_map.items() if fr["correct"] and not cmap[tid]["correct"])
                losses = sum(1 for tid, fr in focal_map.items() if (not fr["correct"]) and cmap[tid]["correct"])
                paired[f"focal_vs_{ctrl}"] = {
                    "focal_wins": wins,
                    "control_wins": losses,
                    "net_wins": wins - losses,
                    "mcnemar_two_sided_p": exact_mcnemar_two_sided_p(wins, losses),
                }
            return {"arms": by_arm, "paired_tests": paired}

        canary_norm_after = float(canary_param.detach().cpu().float().norm().item())
        receipt = {
            "schema": "gamma.reconfiguration.query_swiglu_fastweight.stage2/v1",
            "selected_winner": winner,
            "model_path": str(args.model_path),
            "model_provenance_note": "Qwen3-0.6B-NHS-786708b3 loaded via standard Qwen3ForCausalLM (ttt_proj weights unused); CPT backbone provenance explicitly disclosed.",
            "transforms_sha256": transforms_sha,
            "tasks_sha256": tasks_sha,
            "stage1_receipt_sha256": file_sha256(args.stage1_receipt),
            "dev_families_seed_920001": summarize_subset([r for r in rows if r["group"] == "dev_families"]),
            "holdout_families_seed_930001": summarize_subset([r for r in rows if r["group"] == "holdout_families"]),
            "pooled_128_tasks": summarize_subset(rows),
            "base_weights_unchanged": abs(canary_norm_after - canary_norm_before) == 0.0,
            "concurrent_gpu_processes_pre": pre_procs,
            "concurrent_gpu_processes_post": check_gpu_processes(),
            "peak_rss_bytes": rss_bytes(),
            "rows": rows,
        }
        args.output_json.write_text(json.dumps(receipt, indent=2))
        p_sum = receipt["pooled_128_tasks"]
        print(f"[stage2] DONE winner={winner} | base={p_sum['arms']['base']['correct']}/128 -> focal={p_sum['arms']['focal_fastweight']['correct']}/128 | tests={json.dumps(p_sum['paired_tests'])}")


if __name__ == "__main__":
    main()
