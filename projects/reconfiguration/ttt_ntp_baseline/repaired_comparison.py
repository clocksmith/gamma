"""Fair multi-arm development comparison for the trained Qwen3-0.6B-NHS TTT-NTP baseline.

Strictly labeled as a TRAINED-CHECKPOINT BASELINE (209,715,200 nominal continual-pretraining
tokens across backbone + seven [1024, 1024] ttt_proj matrices). Never conflate with training-free
prompt-conditioned transforms. Preserves the original SEED=831709 fixture and baseline_screen.py
receipts untouched while repairing the single-line record-completion / newline-stop boundary on
a fresh development seed (SEED_V2=942617).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import resource
import sys
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_contract import LAYERS, qualify

SEED_V2 = 942617
NOMINAL_CPT_TOKENS = 209_715_200


def score_single_line(output: str, expected: str) -> bool:
    """Exact normalized match on the generated line; rejects partial, wrong, or verbose text."""
    if not isinstance(output, str) or not expected:
        return False
    first_line = output.split("\n", 1)[0]
    return " ".join(first_line.split()) == expected


def build_fresh_tasks(encode, seed: int = SEED_V2, sibling_mode: str = "none") -> list[dict]:
    """Build 16 fresh development tasks (8 x 4096 + 8 x 8192) matching base record syntax."""
    rng = random.Random(seed)
    tasks = []
    for budget in (4096, 8192):
        for case in range(8):
            if sibling_mode == "none":
                key = f"key_{rng.getrandbits(64):016x}"
                sib_rows = []
                tag = "v2"
            elif sibling_mode == "shared_8hex_stratified":
                n_sib = 3 if (case % 2 == 0) else 1
                stem = f"{rng.getrandbits(32):08x}"
                used_sufs = set()
                sufs = []
                for _ in range(n_sib + 1):
                    while True:
                        sf = f"{rng.getrandbits(32):08x}"
                        if sf not in used_sufs:
                            used_sufs.add(sf)
                            sufs.append(sf)
                            break
                key = f"key_{stem}{sufs[0]}"
                sib_rows = [
                    f"key_{stem}{sf} = value_{rng.getrandbits(64):016x}\n"
                    for sf in sufs[1:]
                ]
                tag = "v3"
            else:
                raise ValueError(f"Unsupported sibling_mode: {sibling_mode}")

            answer = f"value_{rng.getrandbits(64):016x}"
            needle = f"{key} = {answer}\n"
            position = (0.1, 0.5, 0.9)[case % 3]
            prefix = (
                "Exact key-value record table. Complete the value for the final key.\n"
            )
            suffix = f"{key} ="
            rows = list(sib_rows)
            for _ in range(budget):
                row = f"key_{rng.getrandbits(64):016x} = value_{rng.getrandbits(64):016x}\n"
                candidate = rows + [row]
                index = round(len(candidate) * position)
                body = "".join(candidate[:index]) + needle + "".join(candidate[index:])
                prompt = prefix + body + suffix
                ids = encode(prompt)
                if len(ids) > budget:
                    break
                rows = candidate
            if sib_rows:
                rng.shuffle(rows)
            index = round(len(rows) * position)
            body = "".join(rows[:index]) + needle + "".join(rows[index:])
            prompt = prefix + body + suffix
            ids = encode(prompt)
            if not rows or len(ids) > budget:
                raise ValueError("Tokenizer cannot fit repaired retrieval fixture")

            # Precompute half-haystack split prompts for matched-compute no-write baseline
            all_records = rows[:index] + [needle] + rows[index:]
            mid = max(1, len(all_records) // 2)
            half_a = prefix + "".join(all_records[:mid]) + suffix
            half_b = prefix + "".join(all_records[mid:]) + suffix
            tasks.append(
                {
                    "id": f"retrieval-{tag}-{budget}-{case}",
                    "budget": budget,
                    "prompt": prompt,
                    "input_ids": ids,
                    "half_a_ids": encode(half_a),
                    "half_b_ids": encode(half_b),
                    "expected": answer,
                    "key": key,
                    "sibling_distractors": len(sib_rows),
                    "needle_record_fraction": index / len(rows),
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                }
            )
    return tasks


def peak_rss_bytes() -> int:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(ru) if sys.platform == "darwin" else int(ru * 1024)


def fit_ttt_deltas(
    model,
    ttt_projs: dict[int, "torch.Tensor"] | None,
    prompt_ids: "torch.Tensor",
    eta: float = 0.1,
    eta_target: float = 0.1,
    lam: float = 1.0,
    shift: int = 1,
    last_k: int = 8192,
    capture_kv: bool = True,
):
    """Capture normalized MLP inputs across all 7 TTT layers in one forward pass and solve ridge."""
    import torch

    captures = {}
    handles = []

    def make_hook(idx):
        def hook(_mod, inputs, _out):
            captures[idx] = inputs[0].detach()
        return hook

    for idx in LAYERS:
        handles.append(model.model.layers[idx].mlp.register_forward_hook(make_hook(idx)))

    try:
        with torch.inference_mode():
            out = model.model(input_ids=prompt_ids, use_cache=capture_kv, return_dict=True)
            past_kv = out.past_key_values if capture_kv else None
    finally:
        for h in handles:
            h.remove()

    deltas = {}
    norms = {}
    with torch.inference_mode():
        for idx in LAYERS:
            x = captures.pop(idx)  # (1, T, 1024)
            mlp = model.model.layers[idx].mlp
            down = mlp.down_proj
            h_inter = mlp.act_fn(mlp.gate_proj(x)) * mlp.up_proj(x)
            inp_all = h_inter[0].T.to(torch.float32)  # (3072, T)
            W = down.weight.data.to(torch.float32)    # (1024, 3072)
            X_full = inp_all[:, :-shift] if shift > 0 else inp_all
            t_state = x[0].T.to(torch.float32)        # (1024, T)
            if ttt_projs is not None:
                W_proj = ttt_projs[idx].to(torch.float32)
                V_all = W_proj.T @ t_state
            else:
                # Explicit untrained identity-projection ablation
                V_all = t_state
            Y_full = V_all[:, shift:] if shift > 0 else V_all

            if last_k is not None and X_full.shape[1] > last_k:
                X = X_full[:, -last_k:]
                Y = Y_full[:, -last_k:]
            else:
                X = X_full
                Y = Y_full

            residual = Y - W @ X
            Tt = X.shape[1]
            d_inter = X.shape[0]
            if Tt < d_inter:
                G = X.T @ X
                G.diagonal().add_(lam)
                alpha = torch.linalg.solve(G, X.T)
                delta_W = residual @ alpha
            else:
                G = X @ X.T
                G.diagonal().add_(lam)
                rhs = (residual @ X.T).T
                delta_W = torch.linalg.solve(G, rhs).T

            raw_norm = float(delta_W.norm().item())
            w_norm = max(1e-9, float(W.norm().item()))
            raw_ratio = raw_norm / w_norm
            eta_l = min(eta, eta_target / raw_ratio) if raw_ratio > 0 else eta
            scaled = (eta_l * delta_W).to(down.weight.dtype)
            deltas[idx] = scaled
            norms[idx] = float(scaled.float().norm().item())
            del x, h_inter, inp_all, W, X_full, t_state, V_all, Y_full, X, Y, residual, delta_W

    return deltas, norms, past_kv


def greedy_decode_from_logits(model, tokenizer, first_logits, past_kv, max_new_tokens, newline_ids, sync_fn):
    """Greedy decode stopping at newline or EOS, returning generated IDs, mean logprob, and timing."""
    import torch

    log_probs = torch.log_softmax(first_logits[:, -1].float(), dim=-1)
    next_id = first_logits[:, -1].argmax(dim=-1, keepdim=True)
    tok_id = int(next_id.item())
    generated = [tok_id]
    sum_logprob = float(log_probs[0, tok_id].item())
    sync_fn()
    t_first = time.monotonic()

    cache = past_kv
    while (
        len(generated) < max_new_tokens
        and generated[-1] != tokenizer.eos_token_id
        and generated[-1] not in newline_ids
    ):
        res = model(input_ids=next_id, past_key_values=cache, use_cache=True, logits_to_keep=1)
        cache = res.past_key_values
        lp = torch.log_softmax(res.logits[:, -1].float(), dim=-1)
        next_id = res.logits[:, -1].argmax(dim=-1, keepdim=True)
        tok_id = int(next_id.item())
        generated.append(tok_id)
        sum_logprob += float(lp[0, tok_id].item())
        del res

    sync_fn()
    t_end = time.monotonic()
    return generated, sum_logprob / max(1, len(generated)), t_first, t_end


def apply_and_decode_with_restoration(
    model,
    tokenizer,
    backups: dict[int, "torch.Tensor"],
    deltas: dict[int, "torch.Tensor"],
    prompt_ids: "torch.Tensor",
    past_kv,
    norm_preserve: bool,
    max_new_tokens: int,
    newline_ids: set[int],
    sync_fn,
):
    """Apply per-layer deltas, recompute final prompt token on cropped KV cache, decode, and ALWAYS restore."""
    import torch

    max_drift = 0.0
    try:
        with torch.inference_mode():
            for idx, dW in deltas.items():
                w = model.model.layers[idx].mlp.down_proj.weight.data
                w.add_(dW)
                if norm_preserve:
                    init_norm = backups[idx].float().norm(dim=-1, keepdim=True)
                    cur_norm = w.float().norm(dim=-1, keepdim=True).clamp_min(1e-5)
                    w.copy_((w.float() / cur_norm * init_norm).to(w.dtype))

            sync_fn()
            t_gen_start = time.monotonic()
            if past_kv is not None:
                past_kv.crop(prompt_ids.shape[1] - 1)
                res = model(
                    input_ids=prompt_ids[:, -1:],
                    past_key_values=past_kv,
                    use_cache=True,
                    logits_to_keep=1,
                )
            else:
                res = model(input_ids=prompt_ids, use_cache=True, logits_to_keep=1)

            generated, mean_lp, t_first, t_end = greedy_decode_from_logits(
                model, tokenizer, res.logits, res.past_key_values, max_new_tokens, newline_ids, sync_fn
            )
            del res
    finally:
        with torch.inference_mode():
            for idx, orig in backups.items():
                w = model.model.layers[idx].mlp.down_proj.weight.data
                w.copy_(orig)
                drift = float((w.float() - orig.float()).abs().max().item())
                max_drift = max(max_drift, drift)
        if max_drift != 0.0:
            raise RuntimeError(f"Non-zero weight restoration drift: {max_drift}")

    return {
        "generated_ids": generated,
        "mean_logprob": mean_lp,
        "first_token_recompute_seconds": t_first - t_gen_start,
        "decode_interval_seconds": t_end - t_first,
        "max_abs_restore_drift": max_drift,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("tasks_out", type=Path)
    parser.add_argument("result_out", type=Path)
    parser.add_argument("--device", choices=("cpu", "mps"), required=True)
    parser.add_argument("--seed", type=int, default=SEED_V2)
    parser.add_argument(
        "--sibling-mode",
        choices=("none", "shared_8hex_stratified"),
        default="none",
    )
    args = parser.parse_args()

    if args.tasks_out.exists() or args.result_out.exists():
        raise ValueError("Refusing to overwrite existing fixture or result receipt")

    artifact = qualify(args.model)
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(
        args.model, local_files_only=True, trust_remote_code=False, fix_mistral_regex=False
    )
    encode = lambda s: tokenizer.encode(s, add_special_tokens=False)
    tasks = build_fresh_tasks(encode, seed=args.seed, sibling_mode=args.sibling_mode)
    pop_name = "development_v2" if args.sibling_mode == "none" else f"development_v3_{args.sibling_mode}"
    fixture_payload = {"seed": args.seed, "population": pop_name, "tasks": tasks}
    with args.tasks_out.open("x") as stream:
        json.dump(fixture_payload, stream)
    fixture_sha256 = hashlib.sha256(args.tasks_out.read_bytes()).hexdigest()

    newline_ids = {
        tid for tok_str in ("\n", "\r\n", " \n", "\n```")
        for tid in tokenizer.encode(tok_str, add_special_tokens=False)[:1]
    }

    t_load0 = time.monotonic()
    model, info = AutoModelForCausalLM.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=False,
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
        output_loading_info=True,
    )
    expected_keys = {f"model.layers.{i}.mlp.ttt_proj.weight" for i in LAYERS}
    if set(info["unexpected_keys"]) != expected_keys or info["missing_keys"]:
        raise ValueError(f"Unexpected backbone load coverage: {info}")
    model = model.to(args.device).eval()

    raw_st = load_file(str(args.model / "model.safetensors"))
    ttt_projs = {}
    for idx in LAYERS:
        key = f"model.layers.{idx}.mlp.ttt_proj.weight"
        if key not in raw_st:
            raise ValueError(f"Missing trained projection {key}")
        ttt_projs[idx] = raw_st[key].to(device=args.device, dtype=torch.bfloat16)
    del raw_st

    backups = {
        idx: model.model.layers[idx].mlp.down_proj.weight.data.clone()
        for idx in LAYERS
    }

    def sync():
        if args.device == "mps":
            torch.mps.synchronize()

    def mps_allocated() -> int:
        return int(torch.mps.driver_allocated_memory()) if args.device == "mps" else 0

    sync()
    load_seconds = time.monotonic() - t_load0

    arms = [
        "trained_backbone_no_write",
        "ttt_closed_form_write",
        "untrained_identity_ablation",
        "wrong_context_ttt_write",
        "random_norm_matched_write",
        "matched_compute_no_write",
    ]
    logical_ttt_proj_bytes = sum(t.numel() * t.element_size() for t in ttt_projs.values())
    logical_delta_bytes = sum(backups[idx].numel() * backups[idx].element_size() for idx in LAYERS)

    receipt = {
        "schema": "gamma.ttt-ntp-trained-baseline-comparison/v1",
        "classification": "TRAINED-CHECKPOINT BASELINE (not training-free; 209,715,200 nominal CPT tokens)",
        "nominal_continual_pretraining_tokens": NOMINAL_CPT_TOKENS,
        "trained_projection_bytes": logical_ttt_proj_bytes,
        "artifact": artifact,
        "fixture_sha256": fixture_sha256,
        "device": args.device,
        "dtype": "bfloat16",
        "max_new_tokens": 32,
        "ttt_settings": {
            "eta": 0.1,
            "per_layer_eta": True,
            "eta_target": 0.1,
            "lam": 1.0,
            "shift": 1,
            "last_k": 8192,
            "norm_preserve": True,
            "cache_mode": "kv_reuse_crop_T_minus_1_recompute_last_prompt_token",
        },
        "load_seconds": load_seconds,
        "arms": arms,
        "no_write_gate": None,
        "rows": [],
    }
    with args.result_out.open("x") as stream:
        json.dump(receipt, stream)

    # Phase 1: Run trained_backbone_no_write across all 16 tasks first to verify 4..14 feasibility gate
    with torch.inference_mode():
        for task in tasks:
            ids = torch.tensor([task["input_ids"]], device=args.device)
            sync()
            t0 = time.monotonic()
            res = model(input_ids=ids, use_cache=True, logits_to_keep=1)
            gen_ids, mean_lp, t_first, t_end = greedy_decode_from_logits(
                model, tokenizer, res.logits, res.past_key_values, 32, newline_ids, sync
            )
            del res, ids
            text = tokenizer.decode(gen_ids, skip_special_tokens=True)
            row = {
                "id": task["id"],
                "budget": task["budget"],
                "arm": "trained_backbone_no_write",
                "input_tokens": len(task["input_ids"]),
                "generated_ids": gen_ids,
                "output": text,
                "correct": score_single_line(text, task["expected"]),
                "setup_seconds": 0.0,
                "donor_setup_seconds": 0.0,
                "first_token_seconds": t_first - t0,
                "decode_interval_seconds": t_end - t_first,
                "total_seconds": t_end - t0,
                "logical_update_bytes": 0,
                "peak_device_bytes": mps_allocated(),
                "peak_rss_bytes": peak_rss_bytes(),
                "max_abs_restore_drift": 0.0,
            }
            receipt["rows"].append(row)
            args.result_out.write_text(json.dumps(receipt, indent=2))
            print(json.dumps({"phase": "gate", "id": row["id"], "correct": row["correct"], "output": text[:40]}), flush=True)

    base_correct = sum(r["correct"] for r in receipt["rows"])
    gate_pass = 4 <= base_correct <= 14
    receipt["no_write_gate"] = {
        "correct": base_correct,
        "total": len(tasks),
        "pass": gate_pass,
        "rule": "4 <= correct <= 14",
    }
    args.result_out.write_text(json.dumps(receipt, indent=2))
    if not gate_pass:
        receipt["stop_reason"] = f"no-write gate scored {base_correct}/16 outside 4..14"
        args.result_out.write_text(json.dumps(receipt, indent=2))
        return

    # Pre-fit donor deltas once so wrong_context_ttt_write uses next distinct task's exact deltas
    # while charging BOTH donor and recipient setup times explicitly!
    donor_cache = {}
    for i, task in enumerate(tasks):
        ids = torch.tensor([task["input_ids"]], device=args.device)
        sync()
        ts0 = time.monotonic()
        deltas, norms, _ = fit_ttt_deltas(model, ttt_projs, ids, capture_kv=False)
        sync()
        setup_s = time.monotonic() - ts0
        # Move donor deltas to CPU to avoid inflating GPU memory between tasks
        donor_cache[i] = {
            "deltas_cpu": {k: v.cpu() for k, v in deltas.items()},
            "norms": norms,
            "setup_seconds": setup_s,
        }
        del deltas, ids

    other_arms = arms[1:]
    for i, task in enumerate(tasks):
        ids = torch.tensor([task["input_ids"]], device=args.device)
        donor_idx = (i + 1) % len(tasks)
        for j in range(len(other_arms)):
            arm = other_arms[(i + j) % len(other_arms)]

            if arm == "matched_compute_no_write":
                with torch.inference_mode():
                    sync()
                    t0 = time.monotonic()
                    best_cand = None
                    t_first_1 = None
                    for w_idx, half_key in enumerate(("half_a_ids", "half_b_ids")):
                        h_ids = torch.tensor([task[half_key]], device=args.device)
                        res = model(input_ids=h_ids, use_cache=True, logits_to_keep=1)
                        g_ids, m_lp, tf, te = greedy_decode_from_logits(
                            model, tokenizer, res.logits, res.past_key_values, 32, newline_ids, sync
                        )
                        if w_idx == 0:
                            t_first_1 = tf - t0
                        txt = tokenizer.decode(g_ids, skip_special_tokens=True)
                        # Prefer valid value_ format, then higher mean log-probability
                        has_prefix = txt.lstrip().startswith("value_")
                        rank_key = (1 if has_prefix else 0, m_lp)
                        if best_cand is None or rank_key > best_cand["rank_key"]:
                            best_cand = {"gen_ids": g_ids, "text": txt, "rank_key": rank_key, "end": te}
                        del res, h_ids
                    sync()
                    t_done = time.monotonic()
                    row = {
                        "id": task["id"],
                        "budget": task["budget"],
                        "arm": arm,
                        "input_tokens": len(task["half_a_ids"]) + len(task["half_b_ids"]),
                        "generated_ids": best_cand["gen_ids"],
                        "output": best_cand["text"],
                        "correct": score_single_line(best_cand["text"], task["expected"]),
                        "setup_seconds": 0.0,
                        "donor_setup_seconds": 0.0,
                        "first_token_seconds": t_first_1,
                        "decode_interval_seconds": (t_done - t0) - t_first_1,
                        "total_seconds": t_done - t0,
                        "logical_update_bytes": 0,
                        "peak_device_bytes": mps_allocated(),
                        "peak_rss_bytes": peak_rss_bytes(),
                        "max_abs_restore_drift": 0.0,
                    }
            elif arm in ("ttt_closed_form_write", "untrained_identity_ablation"):
                projs = ttt_projs if arm == "ttt_closed_form_write" else None
                sync()
                ts0 = time.monotonic()
                deltas, _, past_kv = fit_ttt_deltas(model, projs, ids, capture_kv=True)
                sync()
                setup_s = time.monotonic() - ts0
                dec = apply_and_decode_with_restoration(
                    model, tokenizer, backups, deltas, ids, past_kv, True, 32, newline_ids, sync
                )
                del deltas, past_kv
                text = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                row = {
                    "id": task["id"],
                    "budget": task["budget"],
                    "arm": arm,
                    "input_tokens": len(task["input_ids"]),
                    "generated_ids": dec["generated_ids"],
                    "output": text,
                    "correct": score_single_line(text, task["expected"]),
                    "setup_seconds": setup_s,
                    "donor_setup_seconds": 0.0,
                    "first_token_seconds": setup_s + dec["first_token_recompute_seconds"],
                    "decode_interval_seconds": dec["decode_interval_seconds"],
                    "total_seconds": setup_s + dec["first_token_recompute_seconds"] + dec["decode_interval_seconds"],
                    "logical_update_bytes": logical_delta_bytes,
                    "peak_device_bytes": mps_allocated(),
                    "peak_rss_bytes": peak_rss_bytes(),
                    "max_abs_restore_drift": dec["max_abs_restore_drift"],
                }
            elif arm == "wrong_context_ttt_write":
                # Capture recipient KV + norms (charged!) AND scale donor's deltas (donor setup also charged!)
                sync()
                ts0 = time.monotonic()
                own_deltas, own_norms, past_kv = fit_ttt_deltas(model, ttt_projs, ids, capture_kv=True)
                del own_deltas
                donor = donor_cache[donor_idx]
                scaled_deltas = {}
                for idx in LAYERS:
                    d_gpu = donor["deltas_cpu"][idx].to(device=args.device, dtype=torch.bfloat16)
                    ratio = own_norms[idx] / max(1e-9, donor["norms"][idx])
                    scaled_deltas[idx] = (d_gpu.float() * ratio).to(torch.bfloat16)
                sync()
                setup_s = time.monotonic() - ts0
                donor_s = donor["setup_seconds"]
                dec = apply_and_decode_with_restoration(
                    model, tokenizer, backups, scaled_deltas, ids, past_kv, True, 32, newline_ids, sync
                )
                del scaled_deltas, past_kv
                text = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                row = {
                    "id": task["id"],
                    "budget": task["budget"],
                    "arm": arm,
                    "donor_id": tasks[donor_idx]["id"],
                    "input_tokens": len(task["input_ids"]),
                    "generated_ids": dec["generated_ids"],
                    "output": text,
                    "correct": score_single_line(text, task["expected"]),
                    "setup_seconds": setup_s,
                    "donor_setup_seconds": donor_s,
                    "first_token_seconds": setup_s + donor_s + dec["first_token_recompute_seconds"],
                    "decode_interval_seconds": dec["decode_interval_seconds"],
                    "total_seconds": setup_s + donor_s + dec["first_token_recompute_seconds"] + dec["decode_interval_seconds"],
                    "logical_update_bytes": logical_delta_bytes,
                    "peak_device_bytes": mps_allocated(),
                    "peak_rss_bytes": peak_rss_bytes(),
                    "max_abs_restore_drift": dec["max_abs_restore_drift"],
                }
            elif arm == "random_norm_matched_write":
                sync()
                ts0 = time.monotonic()
                own_deltas, own_norms, past_kv = fit_ttt_deltas(model, ttt_projs, ids, capture_kv=True)
                del own_deltas
                gen_cpu = torch.Generator(device="cpu").manual_seed(args.seed + i * 101)
                rand_deltas = {}
                for idx in LAYERS:
                    shape = backups[idx].shape
                    r_cpu = torch.randn(shape, generator=gen_cpu, dtype=torch.float32)
                    r_gpu = r_cpu.to(device=args.device)
                    r_norm = max(1e-9, float(r_gpu.norm().item()))
                    rand_deltas[idx] = (r_gpu * (own_norms[idx] / r_norm)).to(torch.bfloat16)
                sync()
                setup_s = time.monotonic() - ts0
                dec = apply_and_decode_with_restoration(
                    model, tokenizer, backups, rand_deltas, ids, past_kv, True, 32, newline_ids, sync
                )
                del rand_deltas, past_kv
                text = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                row = {
                    "id": task["id"],
                    "budget": task["budget"],
                    "arm": arm,
                    "input_tokens": len(task["input_ids"]),
                    "generated_ids": dec["generated_ids"],
                    "output": text,
                    "correct": score_single_line(text, task["expected"]),
                    "setup_seconds": setup_s,
                    "donor_setup_seconds": 0.0,
                    "first_token_seconds": setup_s + dec["first_token_recompute_seconds"],
                    "decode_interval_seconds": dec["decode_interval_seconds"],
                    "total_seconds": setup_s + dec["first_token_recompute_seconds"] + dec["decode_interval_seconds"],
                    "logical_update_bytes": logical_delta_bytes,
                    "peak_device_bytes": mps_allocated(),
                    "peak_rss_bytes": peak_rss_bytes(),
                    "max_abs_restore_drift": dec["max_abs_restore_drift"],
                }

            receipt["rows"].append(row)
            if args.device == "mps":
                torch.mps.empty_cache()
            args.result_out.write_text(json.dumps(receipt, indent=2))
            print(json.dumps({"id": row["id"], "arm": arm, "correct": row["correct"], "total_s": round(row["total_seconds"], 2)}), flush=True)
        del ids
        if args.device == "mps":
            torch.mps.empty_cache()

    # Summarize per-arm quality, timing, memory, and paired wins/losses vs trained_backbone_no_write
    base_by_id = {r["id"]: r for r in receipt["rows"] if r["arm"] == "trained_backbone_no_write"}
    summary = {}
    for arm in arms:
        a_rows = [r for r in receipt["rows"] if r["arm"] == arm]
        c_4k = sum(r["correct"] for r in a_rows if r["budget"] == 4096)
        c_8k = sum(r["correct"] for r in a_rows if r["budget"] == 8192)
        wins = sum(1 for r in a_rows if r["correct"] and not base_by_id[r["id"]]["correct"])
        regressions = sum(1 for r in a_rows if not r["correct"] and base_by_id[r["id"]]["correct"])
        summary[arm] = {
            "correct": c_4k + c_8k,
            "count": len(a_rows),
            "correct_4096": c_4k,
            "correct_8192": c_8k,
            "paired_wins_vs_no_write": wins,
            "paired_regressions_vs_no_write": regressions,
            "mean_setup_seconds": sum(r["setup_seconds"] + r["donor_setup_seconds"] for r in a_rows) / len(a_rows),
            "mean_first_token_seconds": sum(r["first_token_seconds"] for r in a_rows) / len(a_rows),
            "mean_decode_interval_seconds": sum(r["decode_interval_seconds"] for r in a_rows) / len(a_rows),
            "mean_total_seconds": sum(r["total_seconds"] for r in a_rows) / len(a_rows),
            "logical_update_bytes": a_rows[0]["logical_update_bytes"],
            "max_peak_device_bytes": max(r["peak_device_bytes"] for r in a_rows),
            "max_peak_rss_bytes": max(r["peak_rss_bytes"] for r in a_rows),
            "max_abs_restore_drift": max(r["max_abs_restore_drift"] for r in a_rows),
        }
    receipt["summary"] = summary
    receipt["complete"] = True
    args.result_out.write_text(json.dumps(receipt, indent=2))
    print(json.dumps({"summary": summary}, indent=2), flush=True)


if __name__ == "__main__":
    main()
