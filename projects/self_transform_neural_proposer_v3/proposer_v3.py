"""Woodbury Spectral-Kronecker & Split-Half-Coherence Neural Weight-Proposer (`M_Phi_v3`).

Architecture (`1,688` float64 neural parameters across 3 homogeneous matrices, zero `gamma_head`):
- `W_gate`: `(40, 17)` (`16` scale-free structural, curvature & coherence features + homogeneous `1.0`)
- `W_up`:   `(40, 17)`
- `W_out`:  `(8, 41)` (`8` neural update controls over `5` unit-RMS preconditioned basis directions)

Key properties (all computed at ZERO extra target forward-backward passes):
1. **Five Unit-RMS Basis Directions (`[B_grad, B_mom, B_adam, B_kfac, B_spec]`)**:
   Combines raw gradient, bias-corrected momentum, bias-corrected diagonal second-moment (`Adam`),
   exact Woodbury two-sided damped K-FAC (`O(N^3)` when layer width `d >> N`, enabling full-width
   `3584 -> 1024` pretrained Transformer LoRA adaptation in sub-millisecond steps), and 5-step
   Newton-Schulz polar momentum orthogonalization.
2. **Zero Output-Head Shrinkage Loophole**:
   `gamma_head` is completely removed. Every layer uses the identical small L2 weight-decay gate
   `0.03 * sigmoid(ctrl[7])` on non-bias columns only.
3. **Asymmetric Layer/Row Geometry & Coherence Modulation**:
   Reads `log(d_out / d_in)`, `layer_index / max(1, L - 1)`, `is_zero_init_layer`, `step_progress`,
   `log(grad_rms)`, `log(weight_rms + 1e-6)`, and zero-extra-pass split-half gradient coherence
   `cos(G_half1, G_half2)` to modulate per-row step scales (including LoRA+ `lr_B > lr_A` on
   zero-initialized adapter matrices) and damp noisy support updates.
4. **Genuine Multi-Step Self-Modification (`self_modify_proposer_v3`)**:
   Applies `rule_phi` (`Phi_g` in `exact`, `Phi_0` in `fixed_proposer`) across sequential meta-steps
   with persistent `self_opt_state` and NO `trust_radius / rms_all` normalization overwrite (only an
   emergency safety clip at `max_rms = 0.50` that does not bind normal updates).
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import torch
import torch.nn.functional as F

FEAT_DIM_V3 = 16
HID_DIM_V3 = 40
OUT_DIM_V3 = 8


@dataclass
class ProposerWeightsV3:
    W_gate: torch.Tensor  # (40, 17)
    W_up: torch.Tensor    # (40, 17)
    W_out: torch.Tensor   # (8, 41)

    def as_list(self) -> list[torch.Tensor]:
        return [self.W_gate, self.W_up, self.W_out]

    @staticmethod
    def from_list(layers: list[torch.Tensor]) -> "ProposerWeightsV3":
        assert len(layers) == 3
        return ProposerWeightsV3(W_gate=layers[0], W_up=layers[1], W_out=layers[2])

    def clone_detached(self, requires_grad: bool = False) -> "ProposerWeightsV3":
        return ProposerWeightsV3(
            W_gate=self.W_gate.detach().clone().requires_grad_(requires_grad),
            W_up=self.W_up.detach().clone().requires_grad_(requires_grad),
            W_out=self.W_out.detach().clone().requires_grad_(requires_grad),
        )

    def num_parameters(self) -> int:
        return int(self.W_gate.numel() + self.W_up.numel() + self.W_out.numel())

    def to_flat_list(self) -> list[float]:
        return torch.cat([t.detach().reshape(-1) for t in self.as_list()]).double().tolist()

    @staticmethod
    def from_flat_list(vals: list[float], dtype: torch.dtype = torch.float64) -> "ProposerWeightsV3":
        t = torch.tensor(vals, dtype=dtype)
        n1 = HID_DIM_V3 * (FEAT_DIM_V3 + 1)
        n2 = n1 + HID_DIM_V3 * (FEAT_DIM_V3 + 1)
        n3 = n2 + OUT_DIM_V3 * (HID_DIM_V3 + 1)
        assert t.numel() == n3, f"Expected {n3} params, got {t.numel()}"
        return ProposerWeightsV3(
            W_gate=t[:n1].reshape(HID_DIM_V3, FEAT_DIM_V3 + 1).clone(),
            W_up=t[n1:n2].reshape(HID_DIM_V3, FEAT_DIM_V3 + 1).clone(),
            W_out=t[n2:n3].reshape(OUT_DIM_V3, HID_DIM_V3 + 1).clone(),
        )


def init_gen0_proposer_v3(seed: int, dtype: torch.dtype = torch.float64) -> ProposerWeightsV3:
    """Initialize Generation-0 proposer `Phi_0` around a cautious conservative step prior."""
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    s_in = 0.85 / math.sqrt(float(FEAT_DIM_V3 + 1))
    W_gate = s_in * torch.randn((HID_DIM_V3, FEAT_DIM_V3 + 1), generator=gen, dtype=dtype)
    W_up = s_in * torch.randn((HID_DIM_V3, FEAT_DIM_V3 + 1), generator=gen, dtype=dtype)
    W_out = 0.025 * torch.randn((OUT_DIM_V3, HID_DIM_V3 + 1), generator=gen, dtype=dtype)
    W_out[0, -1] = 0.55   # B_grad seed
    W_out[1, -1] = 0.15   # B_mom seed
    W_out[2, -1] = 0.35   # B_adam seed
    W_out[3, -1] = 0.35   # B_kfac seed
    W_out[4, -1] = 0.20   # B_spec seed
    W_out[5, -1] = -2.95  # conservative Gen-0 step-rate logit (`sigmoid(-2.95) ~ 0.0497`)
    W_out[6, -1] = 0.0    # neutral asymmetric row/aspect log-multiplier (`exp(0) = 1.0`)
    W_out[7, -1] = -3.60  # uniform L2 weight decay gate (identical across all layers; zero gamma_head)
    return ProposerWeightsV3(W_gate=W_gate, W_up=W_up, W_out=W_out)


def forward_proposer_v3(
    phi: ProposerWeightsV3,
    feats: torch.Tensor,
    capture_activations: bool = False,
) -> tuple[torch.Tensor, dict[str, torch.Tensor] | None]:
    ones0 = torch.ones((feats.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A0_hom = torch.cat([feats, ones0], dim=-1)                # (R, 17)
    Z_gate = A0_hom @ phi.W_gate.T                            # (R, 40)
    Z_up = A0_hom @ phi.W_up.T                                # (R, 40)
    H_raw = F.silu(Z_gate) * Z_up                             # (R, 40)
    # Parameter-free RMS scaling balances hidden SwiGLU features with homogeneous bias column 1.0
    H1 = 0.30 * H_raw * torch.rsqrt(H_raw.pow(2).mean(dim=-1, keepdim=True) + 0.04)
    ones1 = torch.ones((H1.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A1_hom = torch.cat([H1, ones1], dim=-1)                   # (R, 41)
    Z_out = A1_hom @ phi.W_out.T                              # (R, 8)
    if not capture_activations:
        return Z_out, None
    Z_gate.retain_grad()
    Z_up.retain_grad()
    Z_out.retain_grad()
    return Z_out, {
        "A0_hom": A0_hom.detach(),
        "Z_gate": Z_gate,
        "Z_up": Z_up,
        "A1_hom": A1_hom.detach(),
        "Z_out": Z_out,
    }


def init_opt_state_v3(layers: list[torch.Tensor]) -> dict:
    """Initialize per-target cold optimizer state with spectral-muP geometric layer scales."""
    L = len(layers)
    depth_div = max(1.0, float(L) / 2.5) ** 0.5
    init_rms: list[float] = []
    is_zero_init: list[bool] = []
    base_scales: list[float] = []
    for W in layers:
        w_blk = W.detach()[:, :-1] if W.shape[1] > 1 else W.detach()
        r = float(w_blk.pow(2).mean().sqrt().item())
        d_out, d_in1 = W.shape
        d_in = max(1, d_in1 - 1)
        z_flag = r < 1e-5
        init_rms.append(r)
        is_zero_init.append(z_flag)
        spec_mup = 0.75 / ((float(d_in) * float(d_out)) ** 0.25)
        if z_flag:
            b_s = min(0.60, max(0.03, spec_mup)) / depth_div
        else:
            b_s = min(0.80, max(0.04, max(0.60 * r, spec_mup))) / depth_div
        base_scales.append(b_s)
    return {
        "mom": [torch.zeros_like(W.detach()) for W in layers],
        "mom_live": [torch.zeros_like(W.detach()) for W in layers],
        "rms": [torch.zeros_like(W.detach()) for W in layers],
        "steps_seen": 0,
        "init_layer_rms": init_rms,
        "is_zero_init": is_zero_init,
        "base_scales": base_scales,
        "loss0": None,
        "prev_loss": None,
    }


def _row_cos(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    num = (a * b).sum(dim=-1)
    den = (a.pow(2).sum(dim=-1).sqrt() * b.pow(2).sum(dim=-1).sqrt()).clamp_min(1e-12)
    return (num / den).clamp(-1.0, 1.0)


def _newton_schulz_polar(M_hom: torch.Tensor, steps: int = 5) -> torch.Tensor:
    """Smooth 5-step Newton-Schulz polar orthogonalization on the weight block `M_hom[:, :-1]`."""
    if M_hom.shape[1] <= 1:
        return M_hom
    W_blk = M_hom[:, :-1]
    b_col = M_hom[:, -1:]
    f_norm = W_blk.detach().norm().clamp_min(1e-10)
    X = W_blk / f_norm
    tall = X.shape[0] >= X.shape[1]
    for _ in range(steps):
        if tall:
            X = 1.5 * X - 0.5 * (X @ (X.T @ X))
        else:
            X = 1.5 * X - 0.5 * ((X @ X.T) @ X)
    x_rms = X.detach().pow(2).mean().sqrt().clamp_min(1e-10)
    b_rms = b_col.detach().pow(2).mean().sqrt().clamp_min(1e-10)
    b_scaled = b_col * (x_rms / b_rms)
    return torch.cat([X, b_scaled], dim=-1)


def kfac_woodbury_solve(Mat: torch.Tensor, damp: float, Rhs: torch.Tensor) -> torch.Tensor:
    """Exact solve of `(Cov_norm + damp * I) X = Rhs` (`Cov = Mat.T @ Mat / N`), using Woodbury when `d > 2*N`."""
    N, d = Mat.shape
    diag_mean = (Mat.pow(2).sum(dim=0) / float(N)).mean().clamp_min(1e-8)
    if d <= 2 * N:
        Cov_norm = (Mat.T @ Mat) / (float(N) * diag_mean)
        eye = torch.eye(d, dtype=Mat.dtype, device=Mat.device)
        return torch.linalg.solve(Cov_norm + damp * eye, Rhs)
    Mt = Mat / (float(N) * diag_mean).sqrt()
    eye_n = torch.eye(N, dtype=Mat.dtype, device=Mat.device)
    inner = torch.linalg.solve(damp * eye_n + (Mt @ Mt.T), Mt @ Rhs)
    return (Rhs - Mt.T @ inner) / damp


def compute_five_basis_v3(
    W: torch.Tensor,
    G_live: torch.Tensor,
    G_det: torch.Tensor,
    A: torch.Tensor,
    E: torch.Tensor,
    opt_state: dict,
    l_idx: int,
    k_step: int,
    differentiable_target: bool = False,
):
    """Compute `[B_grad, B_mom, B_adam, B_kfac, B_spec]` shared by `M_Phi_v3` and `kfac_no_proposer`."""
    beta1, beta2 = 0.82, 0.92
    bc1 = 1.0 - (beta1 ** k_step)
    bc2 = 1.0 - (beta2 ** k_step)
    d_out, d_in1 = W.shape
    N = max(2, A.shape[0])

    M_cur = beta1 * opt_state["mom"][l_idx] + (1.0 - beta1) * G_det
    M_live = (beta1 * opt_state["mom_live"][l_idx] + (1.0 - beta1) * G_live) if differentiable_target else M_cur
    V_cur = beta2 * opt_state["rms"][l_idx] + (1.0 - beta2) * (G_det * G_det)
    opt_state["mom"][l_idx] = M_cur.detach()
    opt_state["mom_live"][l_idx] = M_live if differentiable_target else M_cur.detach()
    opt_state["rms"][l_idx] = V_cur.detach()

    M_hat_live = M_live / bc1
    M_hat_det = M_cur / bc1
    V_hat = V_cur / bc2
    D_adam = M_hat_live / (V_hat.sqrt() + 1e-8)

    in_diag = A.pow(2).sum(dim=0) / float(N)
    cond_in = torch.tanh(torch.log((in_diag.max() / (in_diag.mean() + 1e-8)).clamp_min(1.0)) / 4.0)

    damp_in = 0.08 + 0.32 * min(4.0, float(d_in1) / float(N))
    damp_out = 0.14 + 0.24 * min(4.0, float(d_out) / float(N))
    D_in_kron = kfac_woodbury_solve(A, damp_in, G_live.T).T
    D_kfac = kfac_woodbury_solve(E, damp_out, D_in_kron)
    D_spec = _newton_schulz_polar(M_hat_det, steps=5)

    def norm_dir(T_mat: torch.Tensor) -> torch.Tensor:
        return T_mat / (T_mat.pow(2).mean() + 1e-16).sqrt()

    return (
        (norm_dir(G_live), norm_dir(M_hat_live), norm_dir(D_adam), norm_dir(D_kfac), norm_dir(D_spec)),
        (M_hat_det, D_adam.detach(), D_kfac.detach(), cond_in),
        norm_dir,
    )


def propose_update_v3(
    phi: ProposerWeightsV3,
    layers: list[torch.Tensor],
    grads: list[torch.Tensor],
    act_inputs: list[torch.Tensor],
    err_outputs: list[torch.Tensor],
    opt_state: dict,
    step_idx: int,
    total_steps: int,
    cur_loss: torch.Tensor,
    capture_self_acts: list[dict[str, torch.Tensor]] | None = None,
    differentiable_target: bool = False,
    proximal_anchors: list[torch.Tensor] | None = None,
    max_safety_rms: float = 0.50,
) -> list[torch.Tensor]:
    L = len(layers)
    opt_state["steps_seen"] = int(opt_state.get("steps_seen", 0)) + 1
    k_step = opt_state["steps_seen"]

    loss_val = float(cur_loss.detach().item())
    if opt_state["loss0"] is None:
        opt_state["loss0"] = max(abs(loss_val), 1e-8)
    prev_l = opt_state.get("prev_loss")
    step_loss_delta = 0.0 if prev_l is None else ((loss_val - prev_l) / (abs(prev_l) + 1e-8))
    opt_state["prev_loss"] = loss_val if math.isfinite(loss_val) else prev_l

    dtype = layers[0].dtype
    device = layers[0].device
    step_delta_f = torch.tanh(torch.tensor(step_loss_delta, dtype=dtype, device=device))
    loss0 = float(opt_state["loss0"])
    rel_loss_f = torch.tanh(torch.tensor((loss_val - loss0) / (loss0 + 1e-8), dtype=dtype, device=device))
    step_prog = float(step_idx) / max(1.0, float(total_steps - 1))
    cos_env = 0.25 + 0.75 * 0.5 * (1.0 + math.cos(math.pi * step_prog))

    new_layers: list[torch.Tensor] = []
    for l_idx in range(L):
        W = layers[l_idx]
        G_live = grads[l_idx] if differentiable_target else grads[l_idx].detach()
        if differentiable_target and G_live.requires_grad:
            G_live = G_live.clone()
            G_live.register_hook(lambda g: g * (1.5 / g.norm().clamp_min(1.5)))
        G = grads[l_idx].detach()
        A = act_inputs[l_idx].detach()
        E = err_outputs[l_idx].detach()
        d_out, d_in1 = W.shape
        d_in = max(1, d_in1 - 1)
        N = max(2, A.shape[0])
        mid = max(1, N // 2)

        # Split-half per-row gradient coherence at ZERO extra forward-backward passes
        G_h1 = (E[:mid].T @ A[:mid]) / float(mid)
        G_h2 = (E[mid:].T @ A[mid:]) / float(max(1, N - mid))
        half_coherence = _row_cos(G_h1, G_h2)

        (B_grad, B_mom, B_adam, B_kfac, B_spec), (M_hat_det, D_adam_det, D_kfac_det, cond_in), norm_dir = (
            compute_five_basis_v3(W, G_live, G, A, E, opt_state, l_idx, k_step, differentiable_target)
        )

        w_row_rms = W.detach().pow(2).mean(dim=-1).sqrt()
        g_row_rms = G.pow(2).mean(dim=-1).sqrt()
        g_layer_rms = G.pow(2).mean().sqrt().clamp_min(1e-12)

        depth_f = float(l_idx) / max(1.0, float(L - 1))
        log_aspect_io = math.tanh(math.log(float(d_out) / float(d_in)) / 2.5)
        is_zero_f = 1.0 if opt_state["is_zero_init"][l_idx] else 0.0
        sample_aspect_f = math.tanh(math.log(float(d_in1) / float(N)) / 2.0)

        ones_r = torch.ones(d_out, dtype=dtype, device=device)
        feats = torch.stack([
            ones_r * depth_f,                                                      # 0: layer_index / max(1, L - 1)
            ones_r * log_aspect_io,                                                # 1: log(d_out / d_in)
            ones_r * is_zero_f,                                                    # 2: is_zero_init_layer
            ones_r * step_prog,                                                    # 3: step progress t / (B - 1)
            ones_r * rel_loss_f,                                                   # 4: loss ratio vs initial loss
            ones_r * step_delta_f,                                                 # 5: per-step loss delta
            ones_r * sample_aspect_f,                                              # 6: log(d_in1 / N)
            ones_r * cond_in,                                                      # 7: input covariance anisotropy
            half_coherence,                                                        # 8: cos(G_half1, G_half2)
            torch.tanh(torch.log(g_row_rms + 1e-8) / 4.0),                         # 9: log(grad_rms)
            torch.tanh(torch.log(w_row_rms + 1e-6) / 4.0),                         # 10: log(weight_rms + 1e-6)
            torch.tanh(torch.log((g_row_rms + 1e-8) / (w_row_rms + 1e-4)) / 4.0),  # 11: log(grad_rms / weight_rms)
            torch.tanh(torch.log((g_row_rms + 1e-12) / g_layer_rms) / 2.0),        # 12: within-layer row grad ratio
            _row_cos(G, M_hat_det),                                                # 13: cos(grad, mom)
            _row_cos(G, D_adam_det),                                               # 14: cos(grad, adam)
            _row_cos(G, D_kfac_det),                                               # 15: cos(grad, kfac)
        ], dim=-1)                                                                 # (d_out, 16)

        raw_ctrl, cap = forward_proposer_v3(phi, feats, capture_activations=(capture_self_acts is not None))
        if capture_self_acts is not None and cap is not None:
            capture_self_acts.append(cap)

        mix_w = torch.tanh(raw_ctrl[:, 0:5])
        D_comb = (
            mix_w[:, 0:1] * B_grad
            + mix_w[:, 1:2] * B_mom
            + mix_w[:, 2:3] * B_adam
            + mix_w[:, 3:4] * B_kfac
            + mix_w[:, 4:5] * B_spec
        )
        B_comb = norm_dir(D_comb)

        base_scale = float(opt_state["base_scales"][l_idx])
        step_gate = torch.sigmoid(raw_ctrl[:, 5:6])
        row_mult = torch.exp(1.25 * torch.tanh(raw_ctrl[:, 6:7]))
        eta = 0.72 * cos_env * base_scale * step_gate * row_mult

        # Identical L2 weight-decay gate across ALL layers (NO gamma_head anywhere!)
        gamma_wd = 0.03 * torch.sigmoid(raw_ctrl[:, 7:8])
        shrink_mask = torch.ones((1, d_in1), dtype=dtype, device=device)
        shrink_mask[0, -1] = 0.0
        W_reg_target = (W - proximal_anchors[l_idx]) if proximal_anchors is not None else W
        delta_W = -eta * B_comb - (gamma_wd * shrink_mask) * W_reg_target

        step_rms = delta_W.detach().pow(2).mean().sqrt().clamp_min(1e-12)
        if float(step_rms.item()) > max_safety_rms:
            delta_W = delta_W * (max_safety_rms / step_rms)
        new_layers.append(W + delta_W)
        if differentiable_target and new_layers[-1].requires_grad:
            new_layers[-1].register_hook(lambda g: g * (2.0 / g.norm().clamp_min(2.0)))
    return new_layers


def self_modify_proposer_v3(
    parent_phi: ProposerWeightsV3,
    meta_loss: torch.Tensor,
    captured_forwards: list[dict[str, torch.Tensor]],
    self_opt_state: dict,
    meta_step_idx: int,
    total_meta_steps: int,
    proposer_rule_phi: ProposerWeightsV3 | None = None,
    max_rms_safety_clip: float = 0.50,
) -> tuple[ProposerWeightsV3, dict[str, float]]:
    """Apply `proposer_rule_phi` (`Phi_g` for recursive `exact`, `Phi_0` for `fixed_proposer`) to `{W_gate, W_up, W_out}`.

    Preserves `proposer_rule_phi`'s learned step length without `trust_radius / rms_all` normalization
    overwrite; only an emergency safety clip at `max_rms_safety_clip = 0.50` guards against divergence.
    """
    w_list = parent_phi.as_list()
    grads = torch.autograd.grad(meta_loss, w_list, retain_graph=True, allow_unused=False)

    A0_all = torch.cat([c["A0_hom"] for c in captured_forwards], dim=0)
    A1_all = torch.cat([c["A1_hom"] for c in captured_forwards], dim=0)
    z_gates = [c["Z_gate"] for c in captured_forwards]
    z_ups = [c["Z_up"] for c in captured_forwards]
    z_outs = [c["Z_out"] for c in captured_forwards]
    e_all = torch.autograd.grad(meta_loss, z_gates + z_ups + z_outs, retain_graph=False, allow_unused=False)
    n_c = len(captured_forwards)
    E_gate = torch.cat(list(e_all[:n_c]), dim=0)
    E_up = torch.cat(list(e_all[n_c : 2 * n_c]), dim=0)
    E_out = torch.cat(list(e_all[2 * n_c :]), dim=0)

    if A0_all.shape[0] > 512:
        stride = max(1, A0_all.shape[0] // 512)
        A0_all = A0_all[::stride][:512]
        A1_all = A1_all[::stride][:512]
        E_gate = E_gate[::stride][:512]
        E_up = E_up[::stride][:512]
        E_out = E_out[::stride][:512]

    with torch.no_grad():
        rule_source = proposer_rule_phi if proposer_rule_phi is not None else parent_phi
        phi_frozen = rule_source.clone_detached(requires_grad=False)
        anchor_w = [w.detach().clone() for w in w_list]
        raw_updated = propose_update_v3(
            phi=phi_frozen,
            layers=[w.detach().clone() for w in w_list],
            grads=[g.detach() for g in grads],
            act_inputs=[A0_all.detach(), A0_all.detach(), A1_all.detach()],
            err_outputs=[E_gate.detach(), E_up.detach(), E_out.detach()],
            opt_state=self_opt_state,
            step_idx=meta_step_idx,
            total_steps=total_meta_steps,
            cur_loss=meta_loss.detach(),
            capture_self_acts=None,
            differentiable_target=False,
            proximal_anchors=anchor_w,
            max_safety_rms=max_rms_safety_clip,
        )
        deltas = [u - w.detach() for u, w in zip(raw_updated, w_list)]
        rms_all = float(torch.cat([d.reshape(-1) for d in deltas]).pow(2).mean().sqrt().clamp_min(1e-12).item())
        clipped = 1.0 if rms_all > max_rms_safety_clip else 0.0
        scale = min(1.0, float(max_rms_safety_clip) / rms_all)
        updated = [w.detach() + scale * d for w, d in zip(w_list, deltas)]
    return ProposerWeightsV3.from_list(updated), {
        "raw_step_rms": rms_all,
        "safety_clip_triggered": clipped,
    }
