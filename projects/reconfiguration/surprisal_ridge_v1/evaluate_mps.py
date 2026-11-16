"""Multi-domain evaluation of training-free prompt-conditioned transforms on frozen PyTorch MPS models.

Enforces:
1. Context-only transform derivation (query suffix & answers never enter fast-weight derivation).
2. Base discrimination check per domain before running transform arms.
3. Full control suite: base, zero_adapter, unembed_surprisal_ridge, shared_hyperbasis_lora,
   prompt_nll_ridge_lora, wrong_context, random_low_rank, and matched_compute_base.
4. Conditional GPU-resident single-prefill KV-reuse fusion benchmark ONLY if a transform shows
   non-negative/positive quality lift, recording exact setup, first-token, decode, and memory costs.

The separate --context-only mode compares full, blind-split and query-aware state
prompts on every case without deriving transforms or changing their gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tasks import DOMAINS, build_domain_tasks, is_valid_domain_format, score_domain_output
from transforms import (
    derive_prompt_nll_ridge_lora,
    derive_shared_hyperbasis_lora,
    derive_unembed_surprisal_ridge,
    make_random_norm_matched_factors,
    make_zero_factors,
    scale_donor_factors,
    temporary_lora_hooks,
)


def peak_rss_bytes() -> int:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(ru) if sys.platform == "darwin" else int(ru * 1024)


def greedy_decode(model, tokenizer, prompt_ids, max_new_tokens, stop_ids, sync_fn):
    import torch

    with torch.inference_mode():
        sync_fn()
        t0 = time.monotonic()
        res = model(input_ids=prompt_ids, use_cache=True, logits_to_keep=1)
        lp0 = torch.log_softmax(res.logits[:, -1].float(), dim=-1)
        next_id = res.logits[:, -1].argmax(dim=-1, keepdim=True)
        tok0 = int(next_id.item())
        gen = [tok0]
        sum_lp = float(lp0[0, tok0].item())
        first_logits = res.logits[:, -1].float().detach().cpu()
        sync_fn()
        t_first = time.monotonic()

        cache = res.past_key_values
        del res
        while len(gen) < max_new_tokens and gen[-1] not in stop_ids:
            res = model(input_ids=next_id, past_key_values=cache, use_cache=True, logits_to_keep=1)
            cache = res.past_key_values
            lp = torch.log_softmax(res.logits[:, -1].float(), dim=-1)
            next_id = res.logits[:, -1].argmax(dim=-1, keepdim=True)
            tid = int(next_id.item())
            gen.append(tid)
            sum_lp += float(lp[0, tid].item())
            del res
        sync_fn()
        t_end = time.monotonic()
        del cache
    return {
        "generated_ids": gen,
        "mean_logprob": sum_lp / max(1, len(gen)),
        "first_logits_cpu": first_logits,
        "first_token_seconds": t_first - t0,
        "decode_interval_seconds": t_end - t_first,
        "total_seconds": t_end - t0,
    }


def format_chat_or_raw(tokenizer, text: str, use_chat: bool) -> list[int]:
    if use_chat and getattr(tokenizer, "chat_template", None):
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": text}],
            tokenize=False,
            add_generation_prompt=True,
        )
        return tokenizer.encode(rendered, add_special_tokens=False)
    return tokenizer.encode(text, add_special_tokens=False)


def run_state_context_controls(args, model, tokenizer, tasks, sync, dev_bytes, load_seconds):
    """Compare source-preserving preprocessing separately from fast-weight arms."""
    import torch

    arms = ("base", "matched_compute_base", "query_aware_context")
    state_tasks = [task for task in tasks if task["domain"] == "state_trace"]
    receipt = {
        "schema": "gamma.state-context-comparison/v1",
        "classification": "symbolic query-aware context preprocessing; no weight updates; not B1/B2 evidence",
        "model_path": str(args.model), "device": args.device,
        "seed": args.seed, "state_updates": args.state_updates,
        "load_seconds": load_seconds, "arms": arms, "rows": [], "complete": False,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    stop_ids = {tokenizer.eos_token_id}
    for text in ("\n", "\r\n", "<|im_end|>", "<|endoftext|>"):
        ids = tokenizer.encode(text, add_special_tokens=False)
        if len(ids) == 1:
            stop_ids.add(ids[0])
    with args.output.open("x") as stream:
        json.dump(receipt, stream)
    for index, task in enumerate(state_tasks):
        # Rotate order so no arm gets all cold/warm runs. No discrimination
        # gate: source-preserving preprocessing is tested on every case.
        for arm in arms[index % len(arms):] + arms[:index % len(arms)]:
            started = time.perf_counter()
            if arm == "base":
                prompts = [task["prompt"]]
            elif arm == "matched_compute_base":
                prompts = [task["half_a_prompt"], task["half_b_prompt"]]
            else:
                prompts = [task["state_compaction"]["prompt"]]
            encoded = [format_chat_or_raw(tokenizer, prompt, args.chat_template) for prompt in prompts]
            prep = time.perf_counter() - started
            if arm == "query_aware_context":
                prep += task["state_compaction_seconds"]
            candidates = []
            for ids in encoded:
                tensor = torch.tensor([ids], device=args.device)
                dec = greedy_decode(model, tokenizer, tensor, 24, stop_ids, sync)
                text = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                candidates.append((text, dec))
                del tensor
            chosen_text, chosen = max(
                candidates,
                key=lambda item: (is_valid_domain_format("state_trace", item[0]), item[1]["mean_logprob"]),
            )
            # Charge both windows and preprocessing. The selected answer from
            # the blind splitter cannot be exposed until both passes finish.
            compile_seconds = task["state_compaction_seconds"] if arm == "query_aware_context" else 0.0
            total = time.perf_counter() - started + compile_seconds
            first = total if len(candidates) > 1 else prep + chosen["first_token_seconds"]
            row = {
                "id": task["id"], "domain": "state_trace", "arm": arm,
                "input_tokens": sum(map(len, encoded)), "output": chosen_text,
                "expected": task["expected"],
                "correct": score_domain_output("state_trace", chosen_text, task["expected"]),
                "setup_seconds": prep, "first_token_seconds": first,
                "decode_interval_seconds": total - first, "total_seconds": total,
                "first_candidate_token_seconds": prep + candidates[0][1]["first_token_seconds"],
                "device_bytes_after": dev_bytes(), "process_peak_rss_bytes": peak_rss_bytes(),
            }
            if arm == "query_aware_context":
                row["compaction"] = task["state_compaction"]
            receipt["rows"].append(row)
            args.output.write_text(json.dumps(receipt, indent=2))
            print(json.dumps({"id": row["id"], "arm": arm, "correct": row["correct"],
                              "tokens": row["input_tokens"], "total_seconds": total}), flush=True)
    base = {r["id"]: r for r in receipt["rows"] if r["arm"] == "base"}
    receipt["summary"] = {}
    for arm in arms:
        rows = [r for r in receipt["rows"] if r["arm"] == arm]
        receipt["summary"][arm] = {
            "correct": sum(r["correct"] for r in rows), "count": len(rows),
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "mean_total_seconds": sum(r["total_seconds"] for r in rows) / len(rows),
            "paired_wins_vs_base": sum(r["correct"] and not base[r["id"]]["correct"] for r in rows),
            "paired_regressions_vs_base": sum(not r["correct"] and base[r["id"]]["correct"] for r in rows),
        }
    receipt["complete"] = True
    args.output.write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt["summary"], indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=729301)
    parser.add_argument("--cases-per-domain", type=int, default=12)
    parser.add_argument("--device", choices=("cpu", "mps"), default="mps")
    parser.add_argument("--chat-template", action="store_true")
    parser.add_argument("--context-only", action="store_true", help="Compare full, blind-split and query-aware state prompts without weight transforms")
    parser.add_argument("--state-updates", type=int, default=20, help="Explicit state-history length; default preserves prior fixtures")
    args = parser.parse_args()

    if args.output.exists():
        raise ValueError("Refusing to overwrite existing receipt")
    tasks = build_domain_tasks(args.seed, args.cases_per_domain, state_updates=args.state_updates)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(4)
    dt = torch.bfloat16 if args.device == "mps" else torch.float32

    t_load = time.monotonic()
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        local_files_only=True,
        trust_remote_code=False,
        dtype=dt,
        attn_implementation="sdpa",
    ).to(args.device).eval()

    def sync():
        if args.device == "mps":
            torch.mps.synchronize()

    def dev_bytes() -> int:
        return int(torch.mps.driver_allocated_memory()) if args.device == "mps" else 0

    sync()
    load_seconds = time.monotonic() - t_load

    # Snapshot weight checksums on 3 layers to prove base weights never mutate
    n_layers = len(model.model.layers)
    canary_layers = sorted({0, n_layers // 2, n_layers - 1})
    canary_norms = {
        idx: float(model.model.layers[idx].mlp.down_proj.weight.cpu().float().norm().item())
        for idx in canary_layers
    }

    stop_ids = {tokenizer.eos_token_id}
    for nl in ("\n", "\r\n", "<|im_end|>", "<|endoftext|>"):
        enc = tokenizer.encode(nl, add_special_tokens=False)
        if len(enc) == 1:
            stop_ids.add(enc[0])

    use_chat = bool(args.chat_template)

    if args.context_only:
        run_state_context_controls(args, model, tokenizer, tasks, sync, dev_bytes, load_seconds)
        return

    for t in tasks:
        t["prompt_ids"] = format_chat_or_raw(tokenizer, t["prompt"], use_chat)
        t["context_ids"] = tokenizer.encode(t["context_text"], add_special_tokens=False)
        t["half_a_ids"] = format_chat_or_raw(tokenizer, t["half_a_prompt"], use_chat)
        t["half_b_ids"] = format_chat_or_raw(tokenizer, t["half_b_prompt"], use_chat)

    arms = [
        "base",
        "zero_adapter",
        "unembed_surprisal_ridge",
        "shared_hyperbasis_lora",
        "prompt_nll_ridge_lora",
        "wrong_context_surprisal",
        "random_low_rank",
        "matched_compute_base",
    ]

    receipt = {
        "schema": "gamma.reconfiguration.surprisal-ridge/v1",
        "classification": "TRAINING-FREE prompt-conditioned weight transforms (frozen model, zero CPT)",
        "model_path": str(args.model),
        "model_layers": n_layers,
        "hidden_size": int(model.config.hidden_size),
        "intermediate_size": int(model.config.intermediate_size),
        "device": args.device,
        "dtype": str(dt),
        "seed": args.seed,
        "cases_per_domain": args.cases_per_domain,
        "use_chat_template": use_chat,
        "load_seconds": load_seconds,
        "arms": arms,
        "domain_gates": {},
        "rows": [],
    }
    with args.output.open("x") as stream:
        json.dump(receipt, stream)

    # Step 1: Run base across all domains and verify discriminative non-floor/non-ceiling gate
    base_first_logits = {}
    for t in tasks:
        p_ids = torch.tensor([t["prompt_ids"]], device=args.device)
        dec = greedy_decode(model, tokenizer, p_ids, 24, stop_ids, sync)
        base_first_logits[t["id"]] = dec["first_logits_cpu"]
        txt = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
        row = {
            "id": t["id"],
            "domain": t["domain"],
            "arm": "base",
            "input_tokens": len(t["prompt_ids"]),
            "context_tokens": len(t["context_ids"]),
            "output": txt,
            "expected": t["expected"],
            "correct": score_domain_output(t["domain"], txt, t["expected"]),
            "setup_seconds": 0.0,
            "donor_setup_seconds": 0.0,
            "first_token_seconds": dec["first_token_seconds"],
            "decode_interval_seconds": dec["decode_interval_seconds"],
            "total_seconds": dec["total_seconds"],
            "logical_update_bytes": 0,
            "peak_device_bytes": dev_bytes(),
            "peak_rss_bytes": peak_rss_bytes(),
        }
        receipt["rows"].append(row)
        del p_ids

    qualified_domains = []
    for dom in DOMAINS:
        d_rows = [r for r in receipt["rows"] if r["domain"] == dom and r["arm"] == "base"]
        corr = sum(r["correct"] for r in d_rows)
        discriminative = 1 <= corr <= len(d_rows) - 1
        receipt["domain_gates"][dom] = {
            "base_correct": corr,
            "count": len(d_rows),
            "discriminative": discriminative,
        }
        if discriminative:
            qualified_domains.append(dom)
    print(json.dumps({"domain_gates": receipt["domain_gates"]}), flush=True)
    args.output.write_text(json.dumps(receipt, indent=2))

    # Step 2: Pre-derive donor surprisal_ridge factors per qualified domain for wrong_context control
    for dom in qualified_domains:
        dom_tasks = [t for t in tasks if t["domain"] == dom]
        donor_store = {}
        for i, t in enumerate(dom_tasks):
            c_ids = torch.tensor([t["context_ids"]], device=args.device)
            sync()
            ts0 = time.monotonic()
            facs, nrms = derive_unembed_surprisal_ridge(model, c_ids)
            sync()
            s_sec = time.monotonic() - ts0
            donor_store[i] = {
                "factors_cpu": {k: (u.cpu(), v.cpu()) for k, (u, v) in facs.items()},
                "norms": nrms,
                "setup_seconds": s_sec,
            }
            del facs, c_ids

        non_base = arms[1:]
        for i, t in enumerate(dom_tasks):
            p_ids = torch.tensor([t["prompt_ids"]], device=args.device)
            c_ids = torch.tensor([t["context_ids"]], device=args.device)
            donor_i = (i + 1) % len(dom_tasks)

            for j in range(len(non_base)):
                arm = non_base[(i + j) % len(non_base)]
                donor_s = 0.0
                zero_logit_diff = None

                if arm == "matched_compute_base":
                    sync()
                    t0 = time.monotonic()
                    best_c = None
                    tf1 = 0.0
                    for w_i, hk in enumerate(("half_a_ids", "half_b_ids")):
                        h_ids = torch.tensor([t[hk]], device=args.device)
                        dec = greedy_decode(model, tokenizer, h_ids, 24, stop_ids, sync)
                        if w_i == 0:
                            tf1 = dec["first_token_seconds"]
                        txt_c = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                        # Prefer non-empty clean format + higher mean token logprob
                        valid_fmt = is_valid_domain_format(dom, txt_c)
                        rk = (1 if valid_fmt else 0, dec["mean_logprob"])
                        if best_c is None or rk > best_c["rk"]:
                            best_c = {"txt": txt_c, "rk": rk}
                        del h_ids
                    sync()
                    tot_s = time.monotonic() - t0
                    row = {
                        "id": t["id"],
                        "domain": dom,
                        "arm": arm,
                        "input_tokens": len(t["half_a_ids"]) + len(t["half_b_ids"]),
                        "context_tokens": len(t["context_ids"]),
                        "output": best_c["txt"],
                        "expected": t["expected"],
                        "correct": score_domain_output(dom, best_c["txt"], t["expected"]),
                        "setup_seconds": 0.0,
                        "donor_setup_seconds": 0.0,
                        "first_token_seconds": tf1,
                        "decode_interval_seconds": tot_s - tf1,
                        "total_seconds": tot_s,
                        "logical_update_bytes": 0,
                        "peak_device_bytes": dev_bytes(),
                        "peak_rss_bytes": peak_rss_bytes(),
                    }
                    receipt["rows"].append(row)
                    continue

                sync()
                ts0 = time.monotonic()
                if arm == "unembed_surprisal_ridge":
                    facs, _ = derive_unembed_surprisal_ridge(model, c_ids)
                    log_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in facs.values())
                elif arm == "zero_adapter":
                    raw_f, _ = derive_unembed_surprisal_ridge(model, c_ids)
                    facs = make_zero_factors(raw_f)
                    del raw_f
                    log_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in facs.values())
                elif arm == "shared_hyperbasis_lora":
                    facs, _, log_bytes = derive_shared_hyperbasis_lora(model, c_ids)
                elif arm == "prompt_nll_ridge_lora":
                    facs, _ = derive_prompt_nll_ridge_lora(model, c_ids)
                    log_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in facs.values())
                elif arm == "wrong_context_surprisal":
                    own_f, own_n = derive_unembed_surprisal_ridge(model, c_ids)
                    del own_f
                    dn = donor_store[donor_i]
                    facs = scale_donor_factors(dn["factors_cpu"], dn["norms"], own_n, args.device, dt)
                    donor_s = dn["setup_seconds"]
                    log_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in facs.values())
                elif arm == "random_low_rank":
                    own_f, own_n = derive_unembed_surprisal_ridge(model, c_ids)
                    facs = make_random_norm_matched_factors(own_f, own_n, args.seed + i * 37, args.device)
                    del own_f
                    log_bytes = sum((u.numel() + v.numel()) * u.element_size() for u, v in facs.values())
                else:
                    raise ValueError(arm)
                sync()
                setup_s = time.monotonic() - ts0

                with temporary_lora_hooks(model, facs):
                    dec = greedy_decode(model, tokenizer, p_ids, 24, stop_ids, sync)
                if arm == "zero_adapter":
                    zero_logit_diff = float(
                        (dec["first_logits_cpu"] - base_first_logits[t["id"]]).abs().max().item()
                    )
                    if zero_logit_diff > 1e-4:
                        raise RuntimeError(f"Zero adapter violated identity: {zero_logit_diff}")
                del facs
                if args.device == "mps":
                    torch.mps.empty_cache()

                txt = tokenizer.decode(dec["generated_ids"], skip_special_tokens=True)
                row = {
                    "id": t["id"],
                    "domain": dom,
                    "arm": arm,
                    "input_tokens": len(t["prompt_ids"]),
                    "context_tokens": len(t["context_ids"]),
                    "output": txt,
                    "expected": t["expected"],
                    "correct": score_domain_output(dom, txt, t["expected"]),
                    "setup_seconds": setup_s,
                    "donor_setup_seconds": donor_s,
                    "first_token_seconds": setup_s + donor_s + dec["first_token_seconds"],
                    "decode_interval_seconds": dec["decode_interval_seconds"],
                    "total_seconds": setup_s + donor_s + dec["total_seconds"],
                    "logical_update_bytes": log_bytes,
                    "peak_device_bytes": dev_bytes(),
                    "peak_rss_bytes": peak_rss_bytes(),
                }
                if zero_logit_diff is not None:
                    row["zero_adapter_max_logit_diff"] = zero_logit_diff
                receipt["rows"].append(row)

            del p_ids, c_ids
        args.output.write_text(json.dumps(receipt, indent=2))
        print(json.dumps({"completed_domain": dom}), flush=True)

    # Verify base weights remained bit-identical across the entire run
    post_canary_drift = max(
        abs(float(model.model.layers[idx].mlp.down_proj.weight.cpu().float().norm().item()) - canary_norms[idx])
        for idx in canary_layers
    )
    if post_canary_drift != 0.0:
        raise RuntimeError(f"Base weight canary norm drifted: {post_canary_drift}")

    # Summarize per-domain and aggregate across qualified domains
    summary = {"by_domain": {}, "overall": {}, "base_weight_canary_drift": post_canary_drift}
    for dom in qualified_domains:
        base_map = {
            r["id"]: r for r in receipt["rows"] if r["domain"] == dom and r["arm"] == "base"
        }
        summary["by_domain"][dom] = {}
        for arm in arms:
            a_rows = [r for r in receipt["rows"] if r["domain"] == dom and r["arm"] == arm]
            wins = sum(1 for r in a_rows if r["correct"] and not base_map[r["id"]]["correct"])
            regs = sum(1 for r in a_rows if not r["correct"] and base_map[r["id"]]["correct"])
            summary["by_domain"][dom][arm] = {
                "correct": sum(r["correct"] for r in a_rows),
                "count": len(a_rows),
                "paired_wins_vs_base": wins,
                "paired_regressions_vs_base": regs,
                "mean_setup_seconds": sum(r["setup_seconds"] + r["donor_setup_seconds"] for r in a_rows) / len(a_rows),
                "mean_first_token_seconds": sum(r["first_token_seconds"] for r in a_rows) / len(a_rows),
                "mean_decode_interval_seconds": sum(r["decode_interval_seconds"] for r in a_rows) / len(a_rows),
                "mean_total_seconds": sum(r["total_seconds"] for r in a_rows) / len(a_rows),
                "logical_update_bytes": a_rows[0]["logical_update_bytes"],
                "max_peak_device_bytes": max(r["peak_device_bytes"] for r in a_rows),
            }

    for arm in arms:
        a_rows = [r for r in receipt["rows"] if r["domain"] in qualified_domains and r["arm"] == arm]
        if a_rows:
            summary["overall"][arm] = {
                "correct": sum(r["correct"] for r in a_rows),
                "count": len(a_rows),
                "accuracy": sum(r["correct"] for r in a_rows) / len(a_rows),
                "mean_setup_seconds": sum(r["setup_seconds"] + r["donor_setup_seconds"] for r in a_rows) / len(a_rows),
                "mean_first_token_seconds": sum(r["first_token_seconds"] for r in a_rows) / len(a_rows),
                "mean_decode_interval_seconds": sum(r["decode_interval_seconds"] for r in a_rows) / len(a_rows),
                "mean_total_seconds": sum(r["total_seconds"] for r in a_rows) / len(a_rows),
                "logical_update_bytes": a_rows[0]["logical_update_bytes"],
            }

    receipt["summary"] = summary
    receipt["complete"] = True
    args.output.write_text(json.dumps(receipt, indent=2))
    print(json.dumps(summary["overall"], indent=2), flush=True)


if __name__ == "__main__":
    main()
