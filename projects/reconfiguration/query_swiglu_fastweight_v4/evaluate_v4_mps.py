"""PyTorch MPS/CPU evaluator for Gamma Track B1 v4 (`query_swiglu_fastweight_v4`).

Uses `attn_implementation='eager'` on Apple MPS to avoid `sdpa` `bfloat16` `q_len=1`
decode corruption (`argmax=0`), attaches reversible forward hooks on `mlp.down_proj`
(`u + scale * ((z @ A_l) @ B_l)`), and asserts bit-exact `0.0` logit restoration
both at `alpha = 0.0` and after specialty hot-swap + detachment.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from gamma.fastweight import (  # noqa: E402
    ClosedFormLayerLoRA,
    compile_closed_form_layer_lora,
    derive_continuous_cache_knn,
    discover_support_anchors,
    make_random_layer_lora,
)
from regex_baseline_v4 import lookup_support_answer  # noqa: E402


def canonicalize_answer(s: str) -> str:
    t = str(s or "").strip().splitlines()[0].strip() if str(s or "").strip() else ""
    for _ in range(4):
        prev = t
        t = t.rstrip(".,;").strip()
        if len(t) >= 2 and t[0] == t[-1] and t[0] in ("`", '"', "'"):
            t = t[1:-1].strip()
        if t == prev:
            break
    return " ".join(t.split()).lower()


def _get_transformer_layers_and_norms(model: torch.nn.Module):
    base = getattr(model, "model", model)
    if hasattr(base, "language_model"):
        base = base.language_model
    layers = list(base.layers)
    final_norm = getattr(base, "norm", None)
    return layers, final_norm


class ReversibleDownProjHookController:
    """Attaches reversible low-rank `(A_l, B_l)` perturbations to `mlp.down_proj` modules."""

    def __init__(self, layers: list[torch.nn.Module], device: torch.device) -> None:
        self.layers = layers
        self.device = device
        self.active_lora: ClosedFormLayerLoRA | None = None
        self.scale: float = 0.0
        self._handles = []
        for idx, layer in enumerate(layers):
            dp = layer.mlp.down_proj
            self._handles.append(dp.register_forward_hook(self._make_hook(idx)))

    def _make_hook(self, layer_idx: int):
        def _hook(_mod, inputs, output):
            if self.active_lora is None or self.scale == 0.0:
                return output
            pair = self.active_lora.layers.get(layer_idx)
            if pair is None:
                return output
            A_l, B_l = pair
            z = inputs[0].to(torch.float32)
            delta = ((z @ A_l) @ B_l) * float(self.scale)
            return output + delta.to(output.dtype)

        return _hook

    def attach(self, lora: ClosedFormLayerLoRA | None, scale: float = 1.0) -> None:
        if lora is None:
            self.active_lora = None
            self.scale = 0.0
            return
        dev_layers = {
            l_idx: (A_l.to(self.device), B_l.to(self.device))
            for l_idx, (A_l, B_l) in lora.layers.items()
        }
        self.active_lora = ClosedFormLayerLoRA(
            active=lora.active,
            rank=lora.rank,
            d_hidden=lora.d_hidden,
            d_inter=lora.d_inter,
            target_layers=list(lora.target_layers),
            layers=dev_layers,
            uniq_target_tokens=list(lora.uniq_target_tokens),
            anchors_count=lora.anchors_count,
            logical_bytes=lora.logical_bytes,
        )
        self.scale = float(scale)

    def detach(self) -> None:
        self.active_lora = None
        self.scale = 0.0

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles.clear()


@torch.no_grad()
def evaluate_pytorch_v4(model_path: str, output_path: str, device_str: str = "mps", seed: int = 1040001, queries_per_specialty: int = 8) -> dict:
    from tasks_v4 import build_v4_unseen_tasks

    model_p = Path(model_path)
    if not model_p.exists():
        raise FileNotFoundError(
            f"Local model path '{model_path}' is not provisioned on disk (auto-download prohibited by GEMINI.md)."
        )

    device = torch.device(device_str if (device_str != "mps" or torch.backends.mps.is_available()) else "cpu")
    dtype = torch.bfloat16 if device.type in ("mps", "cuda") else torch.float32
    attn_impl = "eager" if device.type == "mps" else "sdpa"

    tok = AutoTokenizer.from_pretrained(str(model_p), local_files_only=True, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(model_p),
        local_files_only=True,
        trust_remote_code=True,
        attn_implementation=attn_impl,
        torch_dtype=dtype,
    ).to(device)
    model.eval()

    layers, final_norm = _get_transformer_layers_and_norms(model)
    num_layers = len(layers)
    has_pfn = hasattr(layers[0], "post_feedforward_layernorm")
    n_top = min(10, num_layers) if has_pfn else min(2, num_layers)
    target_layers = list(range(num_layers - n_top, num_layers))

    d_hidden = int(model.get_output_embeddings().weight.shape[1])
    d_inter = int(layers[target_layers[0]].mlp.down_proj.in_features)
    nl_id = int(tok.encode("\n", add_special_tokens=False)[-1])
    stop_ids = {nl_id}
    if tok.eos_token_id is not None:
        stop_ids.add(int(tok.eos_token_id))

    fn_w = final_norm.weight.detach().float().cpu()
    if "gemma3" in type(model).__name__.lower() or "gemma-3" in str(model_path).lower():
        fn_w = fn_w + 1.0
    pfn_map = {}
    if has_pfn:
        for l_idx in target_layers:
            pw = layers[l_idx].post_feedforward_layernorm.weight.detach().float().cpu()
            if "gemma3" in type(model).__name__.lower() or "gemma-3" in str(model_path).lower():
                pw = pw + 1.0
            pfn_map[l_idx] = pw

    lm_w = model.get_output_embeddings().weight.detach()
    controller = ReversibleDownProjHookController(layers, device)
    tasks = build_v4_unseen_tasks(seed=seed, queries_per_specialty=queries_per_specialty)

    def _capture_z_and_h(ids_1d: list[int]):
        captured: dict[int, torch.Tensor] = {}
        hs = []
        for l_idx in target_layers:
            def _cap(li):
                def _pre(_m, inp):
                    captured[li] = inp[0][0].detach().float().cpu().reshape(-1)
                return _pre
            hs.append(layers[l_idx].mlp.down_proj.register_forward_pre_hook(_cap(l_idx)))
        try:
            inp_t = torch.tensor([ids_1d], device=device, dtype=torch.long)
            out = model(input_ids=inp_t, output_hidden_states=True, use_cache=False)
            h_pre_norm = out.hidden_states[-2][0].detach().float().cpu().reshape(-1) if len(out.hidden_states) >= 2 else out.hidden_states[-1][0].detach().float().cpu().reshape(-1)
            logits_full = out.logits[0].detach().float().cpu()
            return captured, h_pre_norm, logits_full
        finally:
            for h in hs:
                h.remove()

    def _greedy(ids_1d: list[int], max_new: int = 5):
        t0 = time.perf_counter()
        cur = torch.tensor([ids_1d], device=device, dtype=torch.long)
        out = model(input_ids=cur, use_cache=True)
        step0 = out.logits[0, -1].detach().float().cpu()
        past = out.past_key_values
        nid = int(step0.argmax().item())
        gen = [nid]
        while len(gen) < max_new and gen[-1] not in stop_ids:
            nxt = torch.tensor([[gen[-1]]], device=device, dtype=torch.long)
            out = model(input_ids=nxt, past_key_values=past, use_cache=True)
            past = out.past_key_values
            nid = int(out.logits[0, -1].float().argmax().item())
            gen.append(nid)
            if "\n" in tok.decode(gen, skip_special_tokens=True):
                break
        ms = (time.perf_counter() - t0) * 1000.0
        txt = "" if gen[0] in stop_ids else tok.decode(gen, skip_special_tokens=True).strip().splitlines()[0].strip()
        return txt, canonicalize_answer(txt), ms, step0

    specialty_cache = {}
    for idx_s, t in enumerate(tasks):
        sid = t["specialty_id"]
        if sid in specialty_cache:
            specialty_cache[sid]["q_count"] += 1
            continue
        controller.detach()
        t_c0 = time.perf_counter()
        h_ids = tok.encode(t["header_text"], add_special_tokens=False)
        s_ids = tok.encode(t["support_text"], add_special_tokens=False)
        ancs = discover_support_anchors(s_ids, nl_id)
        iso_entries = []
        for ex, a in enumerate(ancs):
            line_ids = h_ids + s_ids[a["line_start"] : a["line_end"]]
            rel_a = len(h_ids) + (a["pos"] - a["line_start"])
            lz, hf, l_all = _capture_z_and_h(line_ids)
            b_top = torch.topk(l_all[rel_a], k=12).indices.tolist() if ex < 4 else []
            iso_entries.append({"line_ids": line_ids, "rel_anchor": rel_a, "h_flat": hf, "layer_z_map": lz, "bare_top": b_top})
        cat_lz, cat_hf, _ = _capture_z_and_h(s_ids)
        sig_map = {}
        if has_pfn:
            for l_idx in target_layers:
                zs = torch.stack([e["layer_z_map"][l_idx][e["rel_anchor"] * d_inter : (e["rel_anchor"] + 1) * d_inter] for e in iso_entries[:6]], dim=0).to(device=device, dtype=dtype)
                u0 = layers[l_idx].mlp.down_proj(zs).float()
                sig_map[l_idx] = float(torch.sqrt((u0 * u0).mean()).item())
        lora = compile_closed_form_layer_lora(
            support_ids=s_ids,
            header_ids=h_ids,
            nl_id=nl_id,
            d_hidden=d_hidden,
            d_inter=d_inter,
            target_layers=target_layers,
            iso_entries=iso_entries,
            cat_entry={"h_flat": cat_hf, "layer_z_map": cat_lz},
            final_norm_g=fn_w,
            get_lm_row=lambda tid: lm_w[tid].float().cpu(),
            post_ffn_norm_map=(pfn_map if has_pfn else None),
            sigma_u0_map=(sig_map if has_pfn else None),
        )
        comp_ms = (time.perf_counter() - t_c0) * 1000.0
        specialty_cache[sid] = {
            "lora": lora,
            "rand_lora": make_random_layer_lora(lora, seed + idx_s * 97),
            "compile_ms": comp_ms,
            "q_count": 1,
        }

    rows = []
    for t in tasks:
        exp = canonicalize_answer(t["expected"])
        sp = specialty_cache[t["specialty_id"]]
        wsp = specialty_cache[t["wrong_specialty_id"]]
        b_ids = tok.encode(t["bare_prompt"], add_special_tokens=False)
        f_ids = tok.encode(t["prompt"], add_special_tokens=False)
        s_ids = tok.encode(t["support_text"], add_special_tokens=False)
        max_new = int(t.get("max_new_tokens", 5))

        controller.detach()
        b_txt, b_can, b_ms, b_l0 = _greedy(b_ids, max_new)
        controller.attach(sp["lora"], scale=0.0)
        z_txt, z_can, z_ms, z_l0 = _greedy(b_ids, max_new)
        zero_diff = float((z_l0 - b_l0).abs().max().item())
        assert zero_diff == 0.0, f"zero != base ({zero_diff})"

        controller.attach(sp["lora"], scale=1.0)
        l_txt, l_can, l_ms, _ = _greedy(b_ids, max_new)
        controller.attach(wsp["lora"], scale=1.0)
        w_txt, w_can, w_ms, _ = _greedy(b_ids, max_new)
        controller.detach()
        rev_txt, rev_can, rev_ms, rev_l0 = _greedy(b_ids, max_new)
        rev_diff = float((rev_l0 - b_l0).abs().max().item())
        assert rev_diff == 0.0, f"revert != base ({rev_diff})"

        c_txt, c_can, c_ms, _ = _greedy(f_ids, max_new)
        controller.attach(sp["lora"], scale=1.0)
        lc_txt, lc_can, lc_ms, _ = _greedy(f_ids, max_new)
        controller.detach()

        rx = lookup_support_answer(t["support_text"], t["query_line"])
        rows.append({
            "task_id": t["task_id"],
            "expected": t["expected"],
            "zero_diff": zero_diff,
            "revert_diff": rev_diff,
            "regime_a_base_correct": b_can == exp,
            "regime_a_lora_correct": l_can == exp,
            "regime_a_wrong_correct": w_can == exp,
            "regime_b_base_correct": c_can == exp,
            "regime_b_lora_correct": lc_can == exp,
            "regime_b_regex_correct": canonicalize_answer(str(rx["answer"])) == exp,
        })

    controller.close()
    out_obj = {"study": "query_swiglu_fastweight_v4", "engine": f"pytorch_{device.type}", "attn_implementation": attn_impl, "rows": rows}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(out_obj, indent=2) + "\n", encoding="utf-8")
    return out_obj


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--seed", type=int, default=1040001)
    ap.add_argument("--queries-per-specialty", type=int, default=8)
    args = ap.parse_args()
    evaluate_pytorch_v4(args.model, args.output, args.device, args.seed, args.queries_per_specialty)
