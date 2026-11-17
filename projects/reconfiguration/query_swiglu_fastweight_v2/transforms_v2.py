"""Frozen v2 prompt-conditioned SwiGLU fast-weight transformation (`C5_v2_unitvar_loonll`).

Advances `v1`'s `C5_portable_et_hl_logitres` with two domain-agnostic mathematical fixes
motivated by the `v1` root-cause trace (without touching any `v2` confirmation tasks):
1. Unit-variance column standardization (`Vc_unit = Vc / v_std`) before supervised `w_snr`
   feature weighting, preventing high-variance full-word distractors from outweighing
   low-variance single-character/subword attribute suffixes (`protoA`, `classA`, `net1`).
2. Per-offset exact leave-one-out cross-entropy step-size selection (`eta_off* in {0, 3, 6, 9, 12}`)
   evaluated directly against `lb_ut` (`base` anchor logits), firing only when held-out context NLL
   improves over `base` by >= 0.04 nats (preventing false-anchor regressions on multi-hop tasks).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import torch
import torch.nn.functional as F

V1_DIR = Path(__file__).resolve().parents[1] / "query_swiglu_fastweight_v1"
if str(V1_DIR) not in sys.path:
    sys.path.insert(0, str(V1_DIR))

from transforms import safe_norm, swiglu


@dataclass
class FastWeightAdapterV2:
    mode: str                                         # 'inactive' | 'window' | 'clause_bigram'
    anchors_count: int
    mu: torch.Tensor | None                           # (1, D)
    v_std: torch.Tensor | None                        # (1, D) or None
    w_snr: torch.Tensor | None                        # (D,) or None
    protos: torch.Tensor | None                       # (M, 3*d) or None
    X_support: torch.Tensor | None                    # (m, D)
    step_etas: dict[int, float]
    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]]  # off -> (u_t: (n_u,), W_down: (n_u, m))
    logical_bytes: int

    def evaluate_query(self, xq_raw: torch.Tensor) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        if self.mode == "inactive" or not self.step_weights or self.X_support is None or self.mu is None:
            return {}
        vqc = xq_raw - self.mu
        if self.v_std is not None:
            vqc = vqc / self.v_std
        if self.w_snr is not None:
            vqc = vqc * self.w_snr.unsqueeze(0)
        xq = safe_norm(vqc)
        q_sims = (xq @ self.X_support.T).cpu()
        q_conf = 1.0
        if self.mode == "clause_bigram":
            max_q_sim = float(q_sims.max().item())
            q_conf = min(1.0, max(0.0, (max_q_sim - 0.58) / 0.27))
            if q_conf <= 0.01:
                return {}
        phi_q = swiglu(4.0 * q_sims - 0.4).squeeze(0).to(xq_raw.device)
        return {off: (u_t, q_conf * (W_d @ phi_q)) for off, (u_t, W_d) in self.step_weights.items()}


def make_zero_adapter_v2(ad: FastWeightAdapterV2) -> FastWeightAdapterV2:
    return FastWeightAdapterV2(
        mode=ad.mode,
        anchors_count=ad.anchors_count,
        mu=ad.mu,
        v_std=ad.v_std,
        w_snr=ad.w_snr,
        protos=ad.protos,
        X_support=ad.X_support,
        step_etas={k: 0.0 for k in ad.step_etas},
        step_weights={off: (u_t, torch.zeros_like(W_d)) for off, (u_t, W_d) in ad.step_weights.items()},
        logical_bytes=ad.logical_bytes,
    )


def make_random_adapter_v2(ad: FastWeightAdapterV2, seed: int) -> FastWeightAdapterV2:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    rand_sw = {}
    for off, (u_t, W_d) in ad.step_weights.items():
        t_norm = float(W_d.float().cpu().norm().item())
        noise = torch.randn(W_d.shape, generator=gen, dtype=torch.float32)
        scaled = noise * (t_norm / max(float(noise.norm().item()), 1e-8))
        rand_sw[off] = (u_t, scaled.to(W_d.device))
    return FastWeightAdapterV2(
        mode=ad.mode,
        anchors_count=ad.anchors_count,
        mu=ad.mu,
        v_std=ad.v_std,
        w_snr=ad.w_snr,
        protos=ad.protos,
        X_support=ad.X_support,
        step_etas=ad.step_etas,
        step_weights=rand_sw,
        logical_bytes=ad.logical_bytes,
    )


def _tensor_bytes(*ts: torch.Tensor | None) -> int:
    return sum(int(t.numel()) * int(t.element_size()) for t in ts if t is not None)


def derive_fastweight_v2(
    prompt_ids: torch.Tensor,
    c_len: int,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
    W_lm_bf16: torch.Tensor,
) -> tuple[FastWeightAdapterV2, torch.Tensor | None]:
    """Derive FastWeightAdapterV2 strictly from context [0 .. c_len-1], plus query feature xq_raw at (T-1)."""
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T, _ = h_last_bf16.shape
    assert 0 < c_len <= T
    if c_len < 24:
        return FastWeightAdapterV2("inactive", 0, None, None, None, None, None, {}, {}, 0), None

    hl = safe_norm(h_last_bf16.float())
    et = safe_norm(E_tok_bf16[p_1d].float())

    lim = max(12, c_len - 12)
    sims_gpu = hl[:lim] @ hl[-1]
    top_v, top_i = torch.topk(sims_gpu, k=min(96, lim))
    p_cpu = p_1d.cpu()
    is_nl_cpu = (p_cpu == newline_id).long()
    line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)

    max_s = float(top_v[0].item())
    anchors: list[int] = []
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
        return FastWeightAdapterV2("inactive", m, None, None, None, None, None, {}, {}, 0), None

    keep_cpu = torch.tensor(anchors, dtype=torch.long)
    keep = keep_cpu.to(device)
    anchor_lines_cpu = line_id_cpu[keep_cpu]

    raw_offsets = []
    y_cols_cpu = []
    for off in range(12):
        pos_c = keep_cpu + off
        if int((pos_c + 1).max().item()) >= c_len:
            break
        assert int((pos_c + 1).max().item()) < c_len
        on_line_c = line_id_cpu[pos_c] == anchor_lines_cpu
        tgts_c = p_cpu[pos_c + 1]
        valid_c = on_line_c & (tgts_c != newline_id)
        n_val = int(valid_c.sum().item())
        if n_val < max(3, m // 4):
            break
        u_t_c = torch.unique(tgts_c[valid_c])
        n_u = int(u_t_c.numel())
        if n_u > 1:
            if n_u <= 16 and n_val == m:
                ind = (tgts_c.unsqueeze(1) == u_t_c.unsqueeze(0)).float()
                y_cols_cpu.append(ind - ind.mean(dim=0, keepdim=True))
            raw_offsets.append((off, pos_c.to(device), valid_c.float().to(device), tgts_c.to(device), u_t_c.to(device)))

    if not raw_offsets:
        return FastWeightAdapterV2("inactive", m, None, None, None, None, None, {}, {}, 0), None

    # Context-only unique answer span ratio (100% query-independent!)
    ans_spans = set()
    for a_idx in anchors:
        a_lid = int(line_id_cpu[a_idx].item())
        span_toks = []
        for pos_s in range(a_idx + 1, min(c_len, a_idx + 9)):
            if int(line_id_cpu[pos_s].item()) != a_lid or int(p_cpu[pos_s].item()) == newline_id:
                break
            span_toks.append(int(p_cpu[pos_s].item()))
        ans_spans.add(tuple(span_toks))
    is_lookup = (len(ans_spans) / float(m) > 0.65) or (not y_cols_cpu)

    v_std: torch.Tensor | None = None
    w_snr: torch.Tensor | None = None
    protos: torch.Tensor | None = None

    if is_lookup:
        mode = "window"
        offs_w = torch.arange(-9, 1, device=device)
        F_a = torch.cat([
            et[keep.unsqueeze(1) + offs_w].reshape(m, -1),
            hl[keep.unsqueeze(1) + offs_w].reshape(m, -1),
        ], dim=-1)
        xq_raw = torch.cat([
            et[(T - 1) + offs_w].reshape(1, -1),
            hl[(T - 1) + offs_w].reshape(1, -1),
        ], dim=-1)
        mu = F_a.mean(dim=0, keepdim=True)
        X = safe_norm(F_a - mu)
    else:
        mode = "clause_bigram"
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
        # Fix 1: Unit-variance column standardization before SNR selection & weighting
        v_std = Vc.pow(2).mean(dim=0, keepdim=True).sqrt().clamp_min(1e-4)
        Vc_unit = Vc / v_std

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

    Phi_cpu = swiglu(4.0 * (X @ X.T).cpu() - 0.4)
    reg = 0.05 * (float(Phi_cpu.pow(2).mean().item()) + 1e-4)
    G_cpu = Phi_cpu.T @ Phi_cpu + reg * torch.eye(m)
    P_dual_cpu = torch.linalg.solve(G_cpu, Phi_cpu.T)
    P_dual = P_dual_cpu.to(device)
    H_hat = (Phi_cpu @ P_dual_cpu).to(device)
    diag_h = H_hat.diagonal().unsqueeze(1)

    step_etas: dict[int, float] = {}
    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for (off, pos_o, valid_f, tgts_o, u_t) in raw_offsets:
        W_ut_f = W_lm_bf16[u_t].float()
        lb_ut = h_last_bf16[pos_o].float() @ W_ut_f.T
        pb_ut = F.softmax(lb_ut, dim=-1)
        y_ut = (u_t.unsqueeze(0) == tgts_o.unsqueeze(1)).float()
        res_ut = valid_f.unsqueeze(1) * (y_ut - pb_ut)

        if is_lookup:
            best_eta = 12.0
        else:
            # Fix 2: Exact leave-one-out cross-entropy calibration against `lb_ut` (`base` anchor logits)
            loo_res = ((H_hat @ res_ut) - diag_h * res_ut) / (1.0 - diag_h).clamp_min(0.1)
            tgt_col = y_ut.argmax(dim=-1)
            valid_bool = valid_f > 0.5
            base_nll = float(F.cross_entropy(lb_ut[valid_bool], tgt_col[valid_bool]).item())
            best_eta = 0.0
            best_nll = base_nll - 0.04  # require >= 0.04 nat held-out NLL gain over base!
            for eta_cand in (3.0, 6.0, 9.0, 12.0):
                cand_nll = float(F.cross_entropy((lb_ut + eta_cand * loo_res)[valid_bool], tgt_col[valid_bool]).item())
                if cand_nll < best_nll:
                    best_nll = cand_nll
                    best_eta = eta_cand

        step_etas[off] = best_eta
        if best_eta > 0.0:
            W_down = best_eta * (res_ut.T @ P_dual)
            step_weights[off] = (u_t, W_down)

    l_bytes = _tensor_bytes(mu, v_std, w_snr, protos, X) + sum(
        _tensor_bytes(u_t, wd) for (u_t, wd) in step_weights.values()
    )
    return FastWeightAdapterV2(
        mode=mode,
        anchors_count=m,
        mu=mu,
        v_std=v_std,
        w_snr=w_snr,
        protos=protos,
        X_support=X,
        step_etas=step_etas,
        step_weights=step_weights,
        logical_bytes=l_bytes,
    ), xq_raw


def extract_query_features_for_donor_v2(
    donor_ad: FastWeightAdapterV2,
    prompt_ids: torch.Tensor,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
) -> torch.Tensor | None:
    if donor_ad.mode == "inactive" or donor_ad.X_support is None:
        return None
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T = int(p_1d.shape[0])
    hl = safe_norm(h_last_bf16.float())
    et = safe_norm(E_tok_bf16[p_1d].float())

    if donor_ad.mode == "window":
        offs_w = torch.arange(-9, 1, device=device)
        return torch.cat([
            et[(T - 1) + offs_w].reshape(1, -1),
            hl[(T - 1) + offs_w].reshape(1, -1),
        ], dim=-1)
    if donor_ad.mode == "clause_bigram" and donor_ad.protos is not None:
        p_cpu = p_1d.cpu()
        is_nl_cpu = (p_cpu == newline_id).long()
        line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)
        max_L = 26
        offs_l_c = torch.arange(-max_L + 1, 1)
        win_q_c = ((T - 1) + offs_l_c).clamp(0, T - 1)
        win_q = win_q_c.to(device)
        et_q_prev = F.pad(et[:-1], (0, 0, 1, 0))
        bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q], 0.4 * et[win_q]], dim=-1))
        mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
        return (bg_q_win @ donor_ad.protos.T).masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values
    return None
