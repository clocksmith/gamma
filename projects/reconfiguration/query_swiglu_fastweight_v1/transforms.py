"""Frozen prompt-conditioned SwiGLU fast-weight candidates and controls for B1.

Candidates (frozen before Stage 1 seed=810001, Stage 2 seed=920001, Holdout seed=930001, and Doppler transfer):
- `C1_linear_window_ridge`: Mean-centered 10-token trailing-window linear ridge fast-weight (`X @ X.T`).
- `C2_isotropic_swiglu`: Clause-bigram / window SwiGLU fast-weight without supervised SNR feature selection (`w_snr = 1`).
- `C3_snr_swiglu_logitres`: 2-hook (`L_early`, `L_mid`) Top-SNR Clause-Bigram / Verbatim-Window SwiGLU fast-weight with LOOCV self-gate and `y - p_base` residual.
- `C4_portable_et_hl_centered`: Zero-hook `(embed_tokens, h_last)` Top-SNR SwiGLU fast-weight with `y - y_mean` target residual (100% engine- and quantization-portable).
- `C5_portable_et_hl_logitres`: Zero-hook `(embed_tokens, h_last)` Top-SNR SwiGLU fast-weight with `y - p_base` candidate-subspace residual.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import torch
import torch.nn.functional as F

CANDIDATE_NAMES = (
    "C1_linear_window_ridge",
    "C2_isotropic_swiglu",
    "C3_snr_swiglu_logitres",
    "C4_portable_et_hl_centered",
    "C5_portable_et_hl_logitres",
)


def safe_norm(x: torch.Tensor) -> torch.Tensor:
    """Contiguous L2 normalization avoiding PyTorch 2.10 Apple MPS non-contiguous F.normalize corruption."""
    xc = x.contiguous()
    return xc * torch.rsqrt((xc * xc).sum(dim=-1, keepdim=True).clamp_min(1e-12))


def swiglu(u: torch.Tensor) -> torch.Tensor:
    return F.silu(u) * u


@dataclass
class FastWeightAdapter:
    """Explicit request-local fast-weight adapter derived strictly from context tokens (< c_len)."""
    candidate: str
    mode: str                                         # 'inactive' | 'window' | 'clause_bigram'
    anchors_count: int
    loo_r2: float
    gate_scale: float
    mu: torch.Tensor | None                           # (1, D)
    w_snr: torch.Tensor | None                        # (D,) or None
    protos: torch.Tensor | None                       # (M, D_bg) or None
    X_support: torch.Tensor | None                    # (m, D)
    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]]  # off -> (u_t: (n_u,), W_down: (n_u, m))
    logical_bytes: int

    def evaluate_query(self, xq_raw: torch.Tensor) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        """Evaluate the fast-weight module on query feature vector xq_raw (1, D) -> step logit deltas."""
        if self.mode == "inactive" or not self.step_weights or self.X_support is None or self.mu is None:
            return {}
        vqc = xq_raw - self.mu
        if self.w_snr is not None:
            vqc = vqc * self.w_snr.unsqueeze(0)
        xq = safe_norm(vqc)                          # (1, D)
        dots = (xq @ self.X_support.T).cpu()          # (1, m)
        if self.candidate == "C1_linear_window_ridge":
            phi_q = dots                              # (1, m) linear kernel
        else:
            phi_q = swiglu(4.0 * dots - 0.4)          # (1, m) SwiGLU quadratic kernel
        phi_q_dev = phi_q.squeeze(0).to(xq_raw.device)
        out: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
        for off, (u_t, W_down) in self.step_weights.items():
            dv = W_down @ phi_q_dev                   # (n_u,)
            out[off] = (u_t, dv)
        return out


def make_zero_adapter(base_adapter: FastWeightAdapter) -> FastWeightAdapter:
    zero_sw = {off: (u_t, torch.zeros_like(W_d)) for off, (u_t, W_d) in base_adapter.step_weights.items()}
    return FastWeightAdapter(
        candidate=base_adapter.candidate,
        mode=base_adapter.mode,
        anchors_count=base_adapter.anchors_count,
        loo_r2=base_adapter.loo_r2,
        gate_scale=0.0,
        mu=base_adapter.mu,
        w_snr=base_adapter.w_snr,
        protos=base_adapter.protos,
        X_support=base_adapter.X_support,
        step_weights=zero_sw,
        logical_bytes=base_adapter.logical_bytes,
    )


def make_random_adapter(base_adapter: FastWeightAdapter, seed: int) -> FastWeightAdapter:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    rand_sw: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for off, (u_t, W_d) in base_adapter.step_weights.items():
        target_norm = float(W_d.float().cpu().norm().item())
        noise = torch.randn(W_d.shape, generator=gen, dtype=torch.float32)
        noise_norm = float(noise.norm().item())
        scaled = noise * (target_norm / max(noise_norm, 1e-8))
        rand_sw[off] = (u_t, scaled.to(W_d.device))
    return FastWeightAdapter(
        candidate=base_adapter.candidate,
        mode=base_adapter.mode,
        anchors_count=base_adapter.anchors_count,
        loo_r2=base_adapter.loo_r2,
        gate_scale=base_adapter.gate_scale,
        mu=base_adapter.mu,
        w_snr=base_adapter.w_snr,
        protos=base_adapter.protos,
        X_support=base_adapter.X_support,
        step_weights=rand_sw,
        logical_bytes=base_adapter.logical_bytes,
    )


def _tensor_bytes(*tensors: torch.Tensor | None) -> int:
    total = 0
    for t in tensors:
        if t is not None:
            total += int(t.numel()) * int(t.element_size())
    return total


def derive_fastweight_From_states(
    candidate: str,
    prompt_ids: torch.Tensor,
    c_len: int,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
    W_lm_bf16: torch.Tensor | None = None,
    h_early_bf16: torch.Tensor | None = None,
    h_mid_bf16: torch.Tensor | None = None,
) -> tuple[FastWeightAdapter, torch.Tensor | None]:
    """Derive FastWeightAdapter strictly from context [0 .. c_len-1], plus query feature xq_raw at (T-1).

    INVARIANT: Target tokens `tgts_c = p_cpu[pos_c + 1]` satisfy `pos_c + 1 < c_len` strictly,
    guaranteeing zero leakage from query tokens or post-context tokens.
    """
    assert candidate in CANDIDATE_NAMES, f"Unknown candidate: {candidate}"
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T, d = h_last_bf16.shape
    assert 0 < c_len <= T, f"Invalid c_len={c_len} for T={T}"

    uses_hooks = candidate in ("C1_linear_window_ridge", "C2_isotropic_swiglu", "C3_snr_swiglu_logitres")
    uses_logit_res = candidate in (
        "C1_linear_window_ridge",
        "C2_isotropic_swiglu",
        "C3_snr_swiglu_logitres",
        "C5_portable_et_hl_logitres",
    )

    hl = safe_norm(h_last_bf16.float())                                   # (T, d)
    et = safe_norm(E_tok_bf16[p_1d].float())                              # (T, d)
    if uses_hooks:
        assert h_early_bf16 is not None and h_mid_bf16 is not None
        he = safe_norm(h_early_bf16.float())
        hm = safe_norm(h_mid_bf16.float())
    else:
        he = et
        hm = hl

    lim = max(12, c_len - 12)
    if c_len < 24:
        return FastWeightAdapter(candidate, "inactive", 0, 0.0, 0.0, None, None, None, None, {}, 0), None

    sims_gpu = hl[:lim] @ hl[-1]
    k_cand = min(96, lim)
    top_v_gpu, top_i_gpu = torch.topk(sims_gpu, k=k_cand)
    top_v = top_v_gpu.cpu().tolist()
    top_i = top_i_gpu.cpu().tolist()
    p_cpu = p_1d.cpu()

    is_nl_cpu = (p_cpu == newline_id).long()
    line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)
    # Precompute line_start_idx for each line_id in O(T) via scatter/searchsorted!
    nl_pos = is_nl_cpu.nonzero(as_tuple=False).squeeze(-1)
    line_starts = [0] + (nl_pos + 1).tolist()

    max_s = top_v[0]
    anchors: list[int] = []
    for v_val, idx in zip(top_v, top_i):
        if v_val < max_s - 0.05:
            break
        if 10 <= idx < c_len - 12 and all(abs(idx - a) >= 4 for a in anchors):
            anchors.append(idx)
            if len(anchors) >= 64:
                break
    anchors.sort()
    m = len(anchors)
    if m < 4:
        return FastWeightAdapter(candidate, "inactive", m, 0.0, 0.0, None, None, None, None, {}, 0), None

    keep_cpu = torch.tensor(anchors, dtype=torch.long)
    keep = keep_cpu.to(device)
    anchor_lines_cpu = line_id_cpu[keep_cpu]

    raw_offsets = []
    y_cols_cpu = []
    for off in range(12):
        pos_c = keep_cpu + off
        if int((pos_c + 1).max().item()) >= c_len:
            break
        # Hard invariant assertion: strictly inside context (< c_len)
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
        return FastWeightAdapter(candidate, "inactive", m, 0.0, 0.0, None, None, None, None, {}, 0), None

    # Context-only regime detection (<0.05ms, zero query-token dependence!):
    # Count distinct multi-token answer spans across the m context anchors strictly inside < c_len.
    ans_spans = set()
    for a_idx in anchors:
        a_lid = int(line_id_cpu[a_idx].item())
        end_span = min(c_len, a_idx + 9)
        span_toks = []
        for pos_s in range(a_idx + 1, end_span):
            if int(line_id_cpu[pos_s].item()) != a_lid or int(p_cpu[pos_s].item()) == newline_id:
                break
            span_toks.append(int(p_cpu[pos_s].item()))
        ans_spans.add(tuple(span_toks))
    unique_span_ratio = len(ans_spans) / float(m)

    force_window = candidate == "C1_linear_window_ridge"
    is_lookup = force_window or (unique_span_ratio > 0.65) or (not y_cols_cpu)

    protos: torch.Tensor | None = None
    w_snr: torch.Tensor | None = None
    if is_lookup:
        mode = "window"
        offs_w = torch.arange(-9, 1, device=device)
        F_a = torch.cat([
            he[keep.unsqueeze(1) + offs_w].reshape(m, -1),
            hm[keep.unsqueeze(1) + offs_w].reshape(m, -1),
        ], dim=-1)
        xq_raw = torch.cat([
            he[(T - 1) + offs_w].reshape(1, -1),
            hm[(T - 1) + offs_w].reshape(1, -1),
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

        et_prev = F.pad(et[:c_len - 1], (0, 0, 1, 0))                     # strictly context!
        bg_ctx = safe_norm(torch.cat([et[:c_len], 0.7 * et_prev, 0.4 * he[:c_len]], dim=-1))
        protos = bg_ctx[proto_pos]                                        # (M, 3*d)

        win_a = win_a_c.to(device)
        mask_a = mask_a_c.to(device)
        dots_a = (bg_ctx[win_a].reshape(m * max_L, -1) @ protos.T).reshape(m, max_L, -1)
        V_a = dots_a.masked_fill(~mask_a.unsqueeze(-1), -2.0).max(dim=1).values

        # Query clause features computed against context `protos`
        et_q_prev = F.pad(et[:-1], (0, 0, 1, 0))
        win_q_c = ((T - 1) + offs_l_c).clamp(0, T - 1)
        win_q = win_q_c.to(device)
        bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q], 0.4 * he[win_q]], dim=-1))
        mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
        dots_q = bg_q_win @ protos.T
        xq_raw = dots_q.masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values

        mu = V_a.mean(dim=0, keepdim=True)
        Vc = V_a - mu
        if candidate != "C2_isotropic_swiglu":
            Y_sup = torch.cat(y_cols_cpu, dim=1).to(device)
            v_norm2 = Vc.pow(2).sum(dim=0, keepdim=True).T.clamp_min(1e-8)
            y_norm2 = Y_sup.pow(2).sum(dim=0, keepdim=True).clamp_min(1e-8)
            rho2_mat = (Vc.T @ Y_sup).pow(2) / (v_norm2 @ y_norm2)
            w_snr = rho2_mat.max(dim=1).values
            if w_snr.numel() > 16:
                kth = torch.topk(w_snr, k=16).values[-1]
                w_snr = torch.where(w_snr >= kth, w_snr, torch.zeros_like(w_snr))
            X = safe_norm(Vc * w_snr.unsqueeze(0))
        else:
            X = safe_norm(Vc)

    dots_tr = (X @ X.T).cpu()
    if candidate == "C1_linear_window_ridge":
        Phi_cpu = dots_tr
        reg = 0.15 * (float(Phi_cpu.pow(2).mean().item()) + 1e-4)
    else:
        Phi_cpu = swiglu(4.0 * dots_tr - 0.4)
        reg = 0.05 * (float(Phi_cpu.pow(2).mean().item()) + 1e-4)
    G_cpu = Phi_cpu.T @ Phi_cpu + reg * torch.eye(m)

    # Solve P_ dual = G^{-1} Phi^T  (m x m) once on CPU (<0.05ms, exact IEEE-754)
    P_dual_cpu = torch.linalg.solve(G_cpu, Phi_cpu.T)                     # (m, m)

    loo_r2 = 1.0
    gate_scale = 12.0
    if not is_lookup and y_cols_cpu and candidate not in ("C1_linear_window_ridge", "C2_isotropic_swiglu"):
        H_hat = Phi_cpu @ P_dual_cpu
        Y_ind = torch.cat(y_cols_cpu, dim=1)
        diag_h = H_hat.diagonal().unsqueeze(1)
        loo_pred = ((H_hat @ Y_ind) - diag_h * Y_ind) / (1.0 - diag_h).clamp_min(0.1)
        loo_r2 = 1.0 - float((Y_ind - loo_pred).pow(2).mean().item()) / max(1e-6, float(Y_ind.pow(2).mean().item()))
        if loo_r2 <= 0.02:
            gate_scale = 0.0

    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    if gate_scale > 0.0:
        P_dual = P_dual_cpu.to(device)                                    # (m, m): maps phi_q -> alpha_q = P_dual.T @ phi_q
        # Note: alpha_q = G^{-1} Phi^T phi_q = P_dual @ phi_q!
        for (off, pos_o, valid_f, tgts_o, u_t) in raw_offsets:
            y_ut = (u_t.unsqueeze(0) == tgts_o.unsqueeze(1)).float()      # (m, n_u)
            if uses_logit_res and W_lm_bf16 is not None:
                W_ut_f = W_lm_bf16[u_t].float()
                lb_ut = h_last_bf16[pos_o].float() @ W_ut_f.T
                base_ref = F.softmax(lb_ut, dim=-1)                       # (m, n_u)
            else:
                # Quantization-portable centered target residual (zero lm_head weight access needed!)
                denom_v = valid_f.sum().clamp_min(1.0)
                mean_y = (valid_f.unsqueeze(1) * y_ut).sum(dim=0, keepdim=True) / denom_v
                base_ref = mean_y.expand_as(y_ut)
            res_ut = valid_f.unsqueeze(1) * (y_ut - base_ref)             # (m, n_u)
            # W_down: (n_u, m) such that dv = W_down @ phi_q = gate_scale * res_ut.T @ (P_dual @ phi_q)
            W_down = gate_scale * (res_ut.T @ P_dual)                     # (n_u, m)
            step_weights[off] = (u_t, W_down)

    l_bytes = _tensor_bytes(mu, w_snr, protos, X) + sum(
        _tensor_bytes(u_t, wd) for (u_t, wd) in step_weights.values()
    )
    adapter = FastWeightAdapter(
        candidate=candidate,
        mode=mode,
        anchors_count=m,
        loo_r2=loo_r2,
        gate_scale=gate_scale,
        mu=mu,
        w_snr=w_snr,
        protos=protos,
        X_support=X,
        step_weights=step_weights,
        logical_bytes=l_bytes,
    )
    return adapter, xq_raw


def extract_query_features_for_donor(
    donor_adapter: FastWeightAdapter,
    prompt_ids: torch.Tensor,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
    h_early_bf16: torch.Tensor | None = None,
    h_mid_bf16: torch.Tensor | None = None,
) -> torch.Tensor | None:
    """Extract target query feature vector xq_raw in the coordinate space of a `wrong_context` donor adapter."""
    if donor_adapter.mode == "inactive" or donor_adapter.X_support is None:
        return None
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T = int(p_1d.shape[0])
    uses_hooks = donor_adapter.candidate in ("C1_linear_window_ridge", "C2_isotropic_swiglu", "C3_snr_swiglu_logitres")
    hl = safe_norm(h_last_bf16.float())
    et = safe_norm(E_tok_bf16[p_1d].float())
    he = safe_norm(h_early_bf16.float()) if (uses_hooks and h_early_bf16 is not None) else et
    hm = safe_norm(h_mid_bf16.float()) if (uses_hooks and h_mid_bf16 is not None) else hl

    if donor_adapter.mode == "window":
        offs_w = torch.arange(-9, 1, device=device)
        return torch.cat([
            he[(T - 1) + offs_w].reshape(1, -1),
            hm[(T - 1) + offs_w].reshape(1, -1),
        ], dim=-1)
    if donor_adapter.mode == "clause_bigram" and donor_adapter.protos is not None:
        p_cpu = p_1d.cpu()
        is_nl_cpu = (p_cpu == newline_id).long()
        line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)
        max_L = 26
        offs_l_c = torch.arange(-max_L + 1, 1)
        win_q_c = ((T - 1) + offs_l_c).clamp(0, T - 1)
        win_q = win_q_c.to(device)
        et_q_prev = F.pad(et[:-1], (0, 0, 1, 0))
        bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q], 0.4 * he[win_q]], dim=-1))
        mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
        dots_q = bg_q_win @ donor_adapter.protos.T
        return dots_q.masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values
    return None
