"""Diagnostic root-cause trace for `medical_dosage_tier` (Item 3).

Strictly uses a fresh diagnostic seed (`seed=777001`, `n=32`, NEVER touching exposed holdout
`seed=930001` or untouched `v2` confirmation `seed=970001`). Quantifies all four candidate mechanisms:
1. **Task semantics (`in_ctx=True` observed `(enzyme, renal)` pair vs `in_ctx=False` unseen pair)**:
   20 random draws from `4x4x4 = 64` leave ~30%–50% of queries with an `(enzyme, renal)` combination
   absent from the context table, requiring factored marginal extrapolation rather than pair lookup.
2. **Answer BPE tokenization merge shift (`DOSE=<syl>-<num>mg`)**:
   In Qwen BPE, `'=tu'`, `'=so'`, `'=fi'`, `'=ce'`, `'=na'`, `'=pe'`, `'=re'`, `'=ru'` merge `'='`
   with the leading consonant (`[' DO', 'SE', '=t', 'u', ...]`), whereas `'=ba'`, `'=ke'`, `'=mo'`,
   `'=va'`, `'=lu'` keep `'='` separate (`[' DO', 'SE', '=', 'ba', ...]`), misaligning token offsets
   within the same context table unless answers start after a clean delimiter (`'DOSE: <syl>-<num>mg'`).
3. **Input tokenization (`bandA..D` / `stage1..4` shared subword stems vs full words)**.
4. **Update rule (`v1_frozen` vs `v2_gated`)**:
   `v1` forced `Top-16` prototypes (admitting `8` spurious `chart` symptom tokens alongside the `8`
   true `enzyme/renal` prototypes) and applied fixed `gate_scale = 12.0` even when query-to-support
   similarity `(xq @ X.T).max()` showed an unseen `(enzyme, renal)` pair (`in_ctx=False`).
   `v2` standardizes columns (`Vc / v_std`), applies a relative SNR noise floor (`w_snr >= 0.28 * max`),
   calibrates `eta*` by exact leave-one-out context NLL, and gates query application by support
   coverage `clamp((max_sim - 0.58) / 0.27, 0.0, 1.0)`.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from score_receipts import is_equivalent_output
from tasks import SYL
from transforms import derive_fastweight_From_states, safe_norm, swiglu


def build_dosage_ablation_variants(seed: int = 777001, n: int = 32) -> dict[str, list[dict]]:
    """Build matched instances (identical RNG draws & latent boolean tables) across 4 encodings."""
    variants = {
        "original": [],
        "bpe_aligned_colon_delim": [],
        "distinct_answer_digits": [],
        "distinct_input_words": [],
    }

    orig_enz = ["bandA", "bandB", "bandC", "bandD"]
    orig_ren = ["stage1", "stage2", "stage3", "stage4"]
    word_enz = ["kinase", "lipase", "protease", "aldolase"]
    word_ren = ["normal", "mild", "moderate", "severe"]
    symptoms = [
        "severe acute headache reported",
        "mild transient fatigue only",
        "no clinical complaints noted",
        "elevated resting pulse spike",
    ]

    rng = random.Random(seed)
    for i in range(n):
        fast_idx = set(rng.sample(range(4), 2))
        low_idx = set(rng.sample(range(4), 2))
        s4 = rng.sample(SYL, 4)
        combos_idx = [(ei, gi, si) for ei in range(4) for gi in range(4) for si in range(4)]
        rng.shuffle(combos_idx)
        demo_idx = combos_idx[:20]
        q_ei, q_gi, q_si = combos_idx[20]
        exact_pair_in_ctx = any((ei == q_ei and gi == q_gi) for (ei, gi, _) in demo_idx)

        for v_name, enz_list, ren_list, prefix, doses in (
            ("original", orig_enz, orig_ren, "DOSE=", ("15mg", "45mg", "10mg", "30mg")),
            ("bpe_aligned_colon_delim", orig_enz, orig_ren, "DOSE: ", ("15mg", "45mg", "10mg", "30mg")),
            ("distinct_answer_digits", orig_enz, orig_ren, "DOSE=", ("12mg", "34mg", "56mg", "78mg")),
            ("distinct_input_words", word_enz, word_ren, "DOSE=", ("15mg", "45mg", "10mg", "30mg")),
        ):
            reg = {
                (True, True): f"{prefix}{s4[0]}-{doses[0]}",
                (True, False): f"{prefix}{s4[1]}-{doses[1]}",
                (False, True): f"{prefix}{s4[2]}-{doses[2]}",
                (False, False): f"{prefix}{s4[3]}-{doses[3]}",
            }
            hdr = "Synthetic trial dosing schedule (determined strictly by enzyme and renal fields):\n"
            rows = [
                f"Case {{enzyme={enz_list[ei]}; renal={ren_list[gi]}; chart='{symptoms[si]}'}} => {reg[(ei in fast_idx, gi in low_idx)]}\n"
                for (ei, gi, si) in demo_idx
            ]
            ctx = hdr + "".join(rows)
            qry = f"Case {{enzyme={enz_list[q_ei]}; renal={ren_list[q_gi]}; chart='{symptoms[q_si]}'}} =>"
            variants[v_name].append({
                "id": f"diag-{v_name}-{i}",
                "context_text": ctx,
                "prompt": ctx + qry,
                "expected": reg[(q_ei in fast_idx, q_gi in low_idx)],
                "exact_pair_in_ctx": exact_pair_in_ctx,
            })
    return variants


def derive_v2_gated_deltas(
    prompt_ids: torch.Tensor,
    c_len: int,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
    W_lm_bf16: torch.Tensor,
) -> tuple[dict[int, tuple[torch.Tensor, torch.Tensor]], dict]:
    """v2 update rule: unit-std standardization + relative SNR noise floor + LOO NLL eta* + support coverage gate."""
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T, _ = h_last_bf16.shape
    hl = safe_norm(h_last_bf16.float())
    et = safe_norm(E_tok_bf16[p_1d].float())

    lim = max(12, c_len - 12)
    sims_gpu = hl[:lim] @ hl[-1]
    top_v, top_i = torch.topk(sims_gpu, k=min(96, lim))
    p_cpu = p_1d.cpu()
    is_nl_cpu = (p_cpu == newline_id).long()
    line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)

    max_s = float(top_v[0].item())
    anchors = []
    for v_val, idx in zip(top_v.cpu().tolist(), top_i.cpu().tolist()):
        if v_val < max_s - 0.05:
            break
        if 10 <= idx < c_len - 12 and all(abs(idx - a) >= 4 for a in anchors):
            anchors.append(idx)
            if len(anchors) >= 64:
                break
    anchors.sort()
    m = len(anchors)
    if m < 4:
        return {}, {"m": m}

    keep_cpu = torch.tensor(anchors, dtype=torch.long)
    anchor_lines_cpu = line_id_cpu[keep_cpu]
    raw_offsets = []
    y_cols_cpu = []
    for off in range(12):
        pos_c = keep_cpu + off
        if int((pos_c + 1).max().item()) >= c_len:
            break
        on_line_c = line_id_cpu[pos_c] == anchor_lines_cpu
        tgts_c = p_cpu[pos_c + 1]
        valid_c = on_line_c & (tgts_c != newline_id)
        n_val = int(valid_c.sum().item())
        if n_val < max(3, m // 4):
            break
        u_t_c = torch.unique(tgts_c[valid_c])
        if u_t_c.numel() > 1:
            if u_t_c.numel() <= 16 and n_val == m:
                ind = (tgts_c.unsqueeze(1) == u_t_c.unsqueeze(0)).float()
                y_cols_cpu.append(ind - ind.mean(dim=0, keepdim=True))
            raw_offsets.append((off, pos_c.to(device), valid_c.float().to(device), tgts_c.to(device), u_t_c.to(device)))

    max_L = 26
    offs_l_c = torch.arange(-max_L + 1, 1)
    win_a_c = (keep_cpu.unsqueeze(1) + offs_l_c).clamp(0, c_len - 1)
    mask_a_c = (line_id_cpu[win_a_c] == anchor_lines_cpu.unsqueeze(1)) & ((keep_cpu.unsqueeze(1) + offs_l_c) >= 0)
    flat_valid_c = win_a_c[mask_a_c]
    pair_id_c = p_cpu[flat_valid_c] * 300007 + p_cpu[(flat_valid_c - 1).clamp_min(0)]
    _, perm_c = torch.sort(pair_id_c)
    sp = pair_id_c[perm_c]
    u_mk = torch.ones_like(sp, dtype=torch.bool)
    if sp.numel() > 1:
        u_mk[1:] = sp[1:] != sp[:-1]
    proto_pos = flat_valid_c[perm_c[u_mk]].to(device)

    et_prev = F.pad(et[:c_len - 1], (0, 0, 1, 0))
    bg_ctx = safe_norm(torch.cat([et[:c_len], 0.7 * et_prev, 0.4 * et[:c_len]], dim=-1))
    protos = bg_ctx[proto_pos]

    dots_a = (bg_ctx[win_a_c.to(device)].reshape(m * max_L, -1) @ protos.T).reshape(m, max_L, -1)
    V_a = dots_a.masked_fill(~mask_a_c.to(device).unsqueeze(-1), -2.0).max(dim=1).values

    et_q_prev = F.pad(et[:-1], (0, 0, 1, 0))
    win_q_c = ((T - 1) + offs_l_c).clamp(0, T - 1)
    win_q = win_q_c.to(device)
    bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q], 0.4 * et[win_q]], dim=-1))
    mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
    xq_raw = (bg_q_win @ protos.T).masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values

    mu = V_a.mean(dim=0, keepdim=True)
    Vc = V_a - mu
    vqc = xq_raw - mu
    v_std = Vc.pow(2).mean(dim=0, keepdim=True).sqrt().clamp_min(1e-4)
    Vc_unit = Vc / v_std
    vqc_unit = vqc / v_std

    Y_sup = torch.cat(y_cols_cpu, dim=1).to(device)
    v_norm2 = Vc_unit.pow(2).sum(dim=0, keepdim=True).T.clamp_min(1e-8)
    y_norm2 = Y_sup.pow(2).sum(dim=0, keepdim=True).clamp_min(1e-8)
    rho2_mat = (Vc_unit.T @ Y_sup).pow(2) / (v_norm2 @ y_norm2)
    w_snr = rho2_mat.max(dim=1).values
    snr_floor = 0.28 * w_snr.max()
    if w_snr.numel() > 16:
        kth = torch.topk(w_snr, k=16).values[-1]
        snr_floor = torch.maximum(snr_floor, kth)
    w_snr = torch.where(w_snr >= snr_floor, w_snr, torch.zeros_like(w_snr))

    X = safe_norm(Vc_unit * w_snr.unsqueeze(0))
    xq = safe_norm(vqc_unit * w_snr.unsqueeze(0))

    q_sims = (xq @ X.T).cpu()
    max_q_sim = float(q_sims.max().item())
    # Confidence gate: full strength when exact causal feature tuple is covered (sim >= 0.85), 0 when unseen (sim <= 0.58)
    q_conf = min(1.0, max(0.0, (max_q_sim - 0.58) / 0.27))

    Phi_cpu = swiglu(4.0 * (X @ X.T).cpu() - 0.4)
    phi_q_cpu = swiglu(4.0 * q_sims - 0.4)
    reg = 0.05 * (float(Phi_cpu.pow(2).mean().item()) + 1e-4)
    G_cpu = Phi_cpu.T @ Phi_cpu + reg * torch.eye(m)
    P_dual_cpu = torch.linalg.solve(G_cpu, Phi_cpu.T)
    H_hat = (Phi_cpu @ P_dual_cpu).to(device)
    diag_h = H_hat.diagonal().unsqueeze(1)
    alpha_q = (P_dual_cpu @ phi_q_cpu.T).squeeze(-1).to(device)

    deltas = {}
    for (off, pos_o, valid_f, tgts_o, u_t) in raw_offsets:
        W_ut_f = W_lm_bf16[u_t].float()
        lb_ut = h_last_bf16[pos_o].float() @ W_ut_f.T
        pb_ut = F.softmax(lb_ut, dim=-1)
        y_ut = (u_t.unsqueeze(0) == tgts_o.unsqueeze(1)).float()
        res_ut = valid_f.unsqueeze(1) * (y_ut - pb_ut)

        loo_res = ((H_hat @ res_ut) - diag_h * res_ut) / (1.0 - diag_h).clamp_min(0.1)
        tgt_col = y_ut.argmax(dim=-1)
        valid_bool = valid_f > 0.5
        base_nll = float(F.cross_entropy(lb_ut[valid_bool], tgt_col[valid_bool]).item())
        best_eta = 0.0
        best_nll = base_nll - 0.04
        for eta_cand in (3.0, 6.0, 9.0, 12.0):
            cand_nll = float(F.cross_entropy((lb_ut + eta_cand * loo_res)[valid_bool], tgt_col[valid_bool]).item())
            if cand_nll < best_nll:
                best_nll = cand_nll
                best_eta = eta_cand
        eff_eta = best_eta * q_conf
        if eff_eta > 0.05:
            deltas[off] = (u_t, eff_eta * (alpha_q @ res_ut))
    return deltas, {"m": m, "max_q_sim": max_q_sim, "q_conf": q_conf}


def main() -> None:
    mp = Path("/Users/xyz/deco/gamma/.work/models/Qwen3-0.6B-NHS-786708b3")
    tok = AutoTokenizer.from_pretrained(mp, local_files_only=True, fix_mistral_regex=False)
    model = AutoModelForCausalLM.from_pretrained(
        mp, local_files_only=True, dtype=torch.bfloat16, attn_implementation="sdpa"
    ).to("mps").eval()
    nl_id = tok.encode("\n", add_special_tokens=False)[0]
    stop_ids = {tok.eos_token_id, nl_id}

    # Record explicit BPE tokenization trace of all 16 SYL values after 'DOSE=' vs 'DOSE: '
    bpe_merge_audit = {"DOSE_eq_merges": [], "DOSE_eq_separate": [], "DOSE_colon_uniform": True}
    for s in SYL:
        t_eq = [tok.decode([i]) for i in tok.encode(f" DOSE={s}-15mg", add_special_tokens=False)]
        t_col = [tok.decode([i]) for i in tok.encode(f" DOSE: {s}-15mg", add_special_tokens=False)]
        if t_eq[2] == "=":
            bpe_merge_audit["DOSE_eq_separate"].append({"syl": s, "tokens": t_eq})
        else:
            bpe_merge_audit["DOSE_eq_merges"].append({"syl": s, "tokens": t_eq})
        if t_col[2] != ":":
            bpe_merge_audit["DOSE_colon_uniform"] = False

    variants = build_dosage_ablation_variants(seed=777001, n=32)
    summary = {"diagnostic_seed": 777001, "n_per_variant": 32, "bpe_tokenization_audit": bpe_merge_audit, "variants": {}}

    with torch.inference_mode():
        for v_name, t_list in variants.items():
            scores = {
                "overall": {"base": 0, "v1_frozen": 0, "v2_gated": 0},
                "in_ctx_true": {"count": 0, "base": 0, "v1_frozen": 0, "v2_gated": 0},
                "in_ctx_false": {"count": 0, "base": 0, "v1_frozen": 0, "v2_gated": 0},
            }
            for t in t_list:
                bucket = "in_ctx_true" if t["exact_pair_in_ctx"] else "in_ctx_false"
                scores[bucket]["count"] += 1
                c_ids = tok.encode(t["context_text"], add_special_tokens=False)
                f_ids = torch.tensor([tok.encode(t["prompt"], add_special_tokens=False)], device="mps")
                c_len = len(c_ids)

                for arm in ("base", "v1_frozen", "v2_gated"):
                    out = model.model(input_ids=f_ids, use_cache=True, return_dict=True)
                    hl_all = out.last_hidden_state[0]
                    cache = out.past_key_values
                    if arm == "base":
                        sd = {}
                    elif arm == "v1_frozen":
                        ad, xq = derive_fastweight_From_states(
                            "C5_portable_et_hl_logitres", f_ids, c_len, nl_id,
                            model.model.embed_tokens.weight, hl_all, model.lm_head.weight,
                        )
                        sd = ad.evaluate_query(xq) if xq is not None else {}
                    else:
                        sd, _ = derive_v2_gated_deltas(
                            f_ids, c_len, nl_id, model.model.embed_tokens.weight, hl_all, model.lm_head.weight
                        )

                    def step_l(hl_vec, k):
                        lf = model.lm_head(hl_vec.unsqueeze(0)).squeeze(0).float()
                        if k in sd:
                            ut, dv = sd[k]
                            lf = lf.clone()
                            lf.index_add_(0, ut, dv.float())
                        return lf

                    l0 = step_l(hl_all[-1], 0)
                    nid = int(l0.argmax().item())
                    gen = [nid]
                    nxt = torch.tensor([[nid]], device="mps")
                    k = 1
                    while len(gen) < 16 and gen[-1] not in stop_ids:
                        rs = model.model(input_ids=nxt, past_key_values=cache, use_cache=True, return_dict=True)
                        cache = rs.past_key_values
                        lk = step_l(rs.last_hidden_state[0, -1], k)
                        nid = int(lk.argmax().item())
                        nxt = torch.tensor([[nid]], device="mps")
                        gen.append(nid)
                        k += 1
                    txt = tok.decode(gen, skip_special_tokens=True)
                    if is_equivalent_output(txt, t["expected"]):
                        scores["overall"][arm] += 1
                        scores[bucket][arm] += 1
                torch.mps.empty_cache()
            summary["variants"][v_name] = scores
            print(f"[dosage-trace] {v_name}: {json.dumps(scores)}", flush=True)

    out_path = Path("/Users/xyz/deco/gamma/.work/query-swiglu-fastweight-v1/dosage_root_cause_trace_seed777001.json")
    out_path.write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
