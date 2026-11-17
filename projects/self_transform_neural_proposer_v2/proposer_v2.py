"""Spectral-Kronecker & Split-Half-Coherence SwiGLU Neural Weight-Proposer (`M_Phi_v2`).

Architecture (`2,073` float64 neural parameters across 3 homogeneous matrices):
- `W_gate`: `(48, 17)` (`16` equivariant structural + generalization features + homogeneous `1.0`)
- `W_up`:   `(48, 17)`
- `W_out`:  `(9, 49)` (`9` neural update controls over `5` matrix basis directions)

Key capabilities (all computed at ZERO extra target forward-backward passes):
1. **Newton-Schulz Polar Spectral Orthogonalization (`B_spectral`)**:
   5-iteration polynomial polar decomposition on layer momentum `M_cur[:, :-1]`, equalizing progress
   across ill-conditioned singular directions in `B = 10` steps without SVD backward singularities.
2. **Dual Input-Activation & Output-Error K-FAC Preconditioning (`B_kfac`, `B_in_k`)**:
   Two-sided Kronecker curvature direction `(Omega_norm + damp_out I)^{-1} G (Sigma_norm + damp_in I)^{-1}`.
3. **Zero-Extra-Pass Split-Half Gradient Coherence (`cos(G_half1, G_half2)`)**:
   Detects noisy-label support memorization directly from `(A, E)` of a single support pass.
4. **Output-Head Temperature Shrinkage (`ctrl[7]`) + Coherence Step Modulation**:
   Prevents noisy classification cross-entropy logit inflation while preserving decision accuracy.
"""
from __future__ import annotations

from dataclasses import dataclass
import torch
import torch.nn.functional as F

FEAT_DIM_V2 = 16
HID_DIM_V2 = 48
OUT_DIM_V2 = 9


@dataclass
class ProposerWeightsV2:
    W_gate: torch.Tensor  # (48, 17)
    W_up: torch.Tensor    # (48, 17)
    W_out: torch.Tensor   # (9, 49)

    def as_list(self) -> list[torch.Tensor]:
        return [self.W_gate, self.W_up, self.W_out]

    @staticmethod
    def from_list(layers: list[torch.Tensor]) -> "ProposerWeightsV2":
        assert len(layers) == 3
        return ProposerWeightsV2(W_gate=layers[0], W_up=layers[1], W_out=layers[2])

    def clone_detached(self, requires_grad: bool = False) -> "ProposerWeightsV2":
        return ProposerWeightsV2(
            W_gate=self.W_gate.detach().clone().requires_grad_(requires_grad),
            W_up=self.W_up.detach().clone().requires_grad_(requires_grad),
            W_out=self.W_out.detach().clone().requires_grad_(requires_grad),
        )

    def num_parameters(self) -> int:
        return int(self.W_gate.numel() + self.W_up.numel() + self.W_out.numel())

    def to_flat_list(self) -> list[float]:
        return torch.cat([t.detach().reshape(-1) for t in self.as_list()]).double().tolist()

    @staticmethod
    def from_flat_list(vals: list[float], dtype: torch.dtype = torch.float64) -> "ProposerWeightsV2":
        t = torch.tensor(vals, dtype=dtype)
        n1 = HID_DIM_V2 * (FEAT_DIM_V2 + 1)
        n2 = n1 + HID_DIM_V2 * (FEAT_DIM_V2 + 1)
        n3 = n2 + OUT_DIM_V2 * (HID_DIM_V2 + 1)
        assert t.numel() == n3, f"Expected {n3} params, got {t.numel()}"
        return ProposerWeightsV2(
            W_gate=t[:n1].reshape(HID_DIM_V2, FEAT_DIM_V2 + 1).clone(),
            W_up=t[n1:n2].reshape(HID_DIM_V2, FEAT_DIM_V2 + 1).clone(),
            W_out=t[n2:n3].reshape(OUT_DIM_V2, HID_DIM_V2 + 1).clone(),
        )


def init_gen0_proposer_v2(seed: int, dtype: torch.dtype = torch.float64) -> ProposerWeightsV2:
    """Initialize Generation-0 proposer `Phi_0` around a conservative raw-gradient baseline."""
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    W_gate = 0.10 * torch.randn((HID_DIM_V2, FEAT_DIM_V2 + 1), generator=gen, dtype=dtype)
    W_up = 0.10 * torch.randn((HID_DIM_V2, FEAT_DIM_V2 + 1), generator=gen, dtype=dtype)
    W_out = 0.06 * torch.randn((OUT_DIM_V2, HID_DIM_V2 + 1), generator=gen, dtype=dtype)
    W_out[0, -1] = 0.90   # pure raw-grad initial direction (`B_comb` is unit-RMS normalized)
    W_out[1, -1] = 0.0    # momentum (unlocked across generations)
    W_out[2, -1] = 0.0    # diag RMS (unlocked across generations)
    W_out[3, -1] = 0.0    # Kronecker/K-FAC (0.0 at Gen-0; unlocked > 0 across generations)
    W_out[4, -1] = -3.15  # conservative Gen-0 step size logit (`sigmoid(-3.15) ~ 0.041`)
    W_out[5, -1] = 0.50   # K-FAC vs input-Kronecker blend logit
    W_out[6, -1] = -3.10  # proximal L2 shrinkage logit
    W_out[7, -1] = -2.50  # output-head temperature damping logit
    W_out[8, -1] = 0.0    # Newton-Schulz spectral orthogonalized basis weight
    return ProposerWeightsV2(W_gate=W_gate, W_up=W_up, W_out=W_out)


def forward_proposer_v2(
    phi: ProposerWeightsV2,
    feats: torch.Tensor,
    capture_activations: bool = False,
) -> tuple[torch.Tensor, dict[str, torch.Tensor] | None]:
    ones0 = torch.ones((feats.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A0_hom = torch.cat([feats, ones0], dim=-1)                # (R, 17)
    Z_gate = A0_hom @ phi.W_gate.T                            # (R, 48)
    Z_up = A0_hom @ phi.W_up.T                                # (R, 48)
    H1 = F.silu(Z_gate) * Z_up                                # (R, 48)
    ones1 = torch.ones((H1.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A1_hom = torch.cat([H1, ones1], dim=-1)                   # (R, 49)
    Z_out = A1_hom @ phi.W_out.T                              # (R, 9)
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


def init_opt_state_v2(layers: list[torch.Tensor]) -> dict:
    return {
        "mom": [torch.zeros_like(W.detach()) for W in layers],
        "mom_live": [torch.zeros_like(W.detach()) for W in layers],
        "rms": [torch.zeros_like(W.detach()) for W in layers],
        "init_layer_rms": [
            float(
                (W.detach()[:, :-1] if W.shape[1] > 1 else W.detach())
                .pow(2).mean().sqrt().clamp(0.03, 1.6).item()
            )
            for W in layers
        ],
        "loss0": None,
        "prev_loss": None,
    }


def _row_cos(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    num = (a * b).sum(dim=-1)
    den = (a.pow(2).sum(dim=-1).sqrt() * b.pow(2).sum(dim=-1).sqrt()).clamp_min(1e-12)
    return (num / den).clamp(-1.0, 1.0)


def _newton_schulz_polar(M_hom: torch.Tensor, steps: int = 5) -> torch.Tensor:
    """Smooth 5-step Newton-Schulz orthogonalization on the weight block `M_hom[:, :-1]`."""
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
    b_scaled = b_col / b_col.detach().pow(2).mean().sqrt().clamp_min(1e-10) * X.detach().pow(2).mean().sqrt().clamp_min(1e-10)
    return torch.cat([X, b_scaled], dim=-1)


def propose_update_v2(
    phi: ProposerWeightsV2,
    layers: list[torch.Tensor],
    grads: list[torch.Tensor],
    act_inputs: list[torch.Tensor],
    err_outputs: list[torch.Tensor],
    opt_state: dict,
    step_idx: int,
    total_steps: int,
    cur_loss: torch.Tensor,
    capture_self_acts: list[dict[str, torch.Tensor]] | None = None,
    max_trust_step: float = 0.26,
    differentiable_target: bool = False,
    proximal_anchors: list[torch.Tensor] | None = None,
) -> list[torch.Tensor]:
    L = len(layers)
    depth_trust = max_trust_step / (max(1.0, float(L) / 2.0) ** 0.5)
    loss_val = float(cur_loss.detach().item())
    if opt_state["loss0"] is None:
        opt_state["loss0"] = max(loss_val, 1e-8)
    prev_l = opt_state.get("prev_loss")
    step_loss_delta = 0.0 if prev_l is None else ((loss_val - prev_l) / (abs(prev_l) + 1e-8))
    opt_state["prev_loss"] = loss_val if (loss_val == loss_val) else prev_l
    step_delta_f = torch.tanh(torch.tensor(step_loss_delta, dtype=layers[0].dtype))
    loss0 = float(opt_state["loss0"])
    rel_loss = torch.tanh(torch.tensor((loss_val - loss0) / (loss0 + 1e-8), dtype=layers[0].dtype))

    new_layers: list[torch.Tensor] = []
    for l_idx in range(L):
        W = layers[l_idx]
        G_live = grads[l_idx] if differentiable_target else grads[l_idx].detach()
        G = grads[l_idx].detach()
        A = act_inputs[l_idx].detach()                        # (N, d_in1)
        E = err_outputs[l_idx].detach()                       # (N, d_out)
        d_out, d_in1 = W.shape
        N = max(2, A.shape[0])
        mid = max(1, N // 2)

        # Split-half per-neuron gradient coherence at ZERO extra forward-backward passes
        G_h1 = (E[:mid].T @ A[:mid]) / float(mid)
        G_h2 = (E[mid:].T @ A[mid:]) / float(max(1, N - mid))
        half_coherence = _row_cos(G_h1, G_h2)                 # (d_out,) in [-1, 1]

        M_cur = 0.82 * opt_state["mom"][l_idx] + 0.18 * G
        M_live = (0.82 * opt_state["mom_live"][l_idx] + 0.18 * G_live) if differentiable_target else M_cur
        V_cur = 0.88 * opt_state["rms"][l_idx] + 0.12 * (G * G)
        opt_state["mom"][l_idx] = M_cur.detach()
        opt_state["mom_live"][l_idx] = M_live if differentiable_target else M_cur.detach()
        opt_state["rms"][l_idx] = V_cur.detach()

        Sigma = (A.T @ A) / float(N)
        Sigma_norm = Sigma / Sigma.diagonal().mean().clamp_min(1e-8)
        cond_in = torch.tanh(torch.log((Sigma.diagonal().max() / (Sigma.diagonal().mean() + 1e-8)).clamp_min(1.0)) / 4.0)

        Omega = (E.T @ E) / float(N)
        Omega_norm = Omega / Omega.diagonal().mean().clamp_min(1e-8)

        eye_in = torch.eye(d_in1, dtype=W.dtype, device=W.device)
        eye_out = torch.eye(d_out, dtype=W.dtype, device=W.device)
        # Marchenko-Pastur sample-aspect damping prevents rank-deficient covariance amplification when d_in1 >= N
        damp_in = 0.08 + 0.36 * (float(d_in1) / float(N))
        damp_out = 0.16 + 0.24 * (float(d_out) / float(N))
        D_in_kron = torch.linalg.solve(Sigma_norm + damp_in * eye_in, G_live.T).T
        D_kfac = torch.linalg.solve(Omega_norm + damp_out * eye_out, D_in_kron)
        D_kfac_det = D_kfac.detach()
        D_spec = _newton_schulz_polar(M_live)

        def norm_dir(T_mat: torch.Tensor) -> torch.Tensor:
            return T_mat / T_mat.detach().pow(2).mean().sqrt().clamp_min(1e-10)

        B_grad = norm_dir(G_live)
        B_mom = norm_dir(M_live)
        B_rms = norm_dir(G_live / (V_cur.sqrt() + 1e-8))
        B_in_k = norm_dir(D_in_kron)
        B_kfac = norm_dir(D_kfac)
        B_spec = norm_dir(D_spec)

        w_row_norm = W.detach().pow(2).mean(dim=-1).sqrt().clamp_min(1e-8)
        g_row_norm = G.pow(2).mean(dim=-1).sqrt().clamp_min(1e-12)
        m_row_norm = M_cur.pow(2).mean(dim=-1).sqrt().clamp_min(1e-12)
        act_rms = (A[:, :-1] if d_in1 > 1 else A).pow(2).mean().sqrt().clamp_min(1e-6)
        out_scale_f = torch.tanh(torch.log((float(d_in1) ** 0.5) * act_rms * w_row_norm + 1e-8) / 3.0)
        e_row_rms = E.pow(2).mean(dim=0).sqrt()
        e_rel = (e_row_rms / e_row_rms.mean().clamp_min(1e-8)).clamp(0.0, 4.0) / 2.0 - 0.5

        depth_f = float(l_idx) / max(1.0, float(L - 1))
        total_L_f = torch.log(torch.tensor(float(L), dtype=W.dtype)) / 2.0
        is_head_f = 1.0 if (l_idx == L - 1) else 0.0
        step_f = float(step_idx) / max(1.0, float(total_steps - 1))
        aspect_f = torch.tanh(torch.log(torch.tensor(float(d_in1) / float(N), dtype=W.dtype)) / 2.0)

        ones_r = torch.ones(d_out, dtype=W.dtype, device=W.device)
        feats = torch.stack([
            ones_r * depth_f,                                                  # 0: relative layer depth
            ones_r * is_head_f,                                                # 1: output head indicator
            ones_r * step_f,                                                   # 2: step progress
            ones_r * step_delta_f,                                             # 3: per-step loss change signal
            ones_r * aspect_f,                                                 # 4: log(d_in1 / N) sample aspect ratio
            ones_r * total_L_f,                                                # 5: log total network depth L
            ones_r * rel_loss,                                                 # 6: relative loss ratio
            ones_r * cond_in,                                                  # 7: activation conditioning
            half_coherence,                                                    # 8: split-half gradient coherence
            out_scale_f,                                                       # 9: log pre-activation output scale (muP temperature)
            torch.tanh(torch.log(g_row_norm / w_row_norm) / 4.0),              # 10: log grad/weight ratio
            torch.tanh(torch.log(g_row_norm / g_row_norm.mean().clamp_min(1e-12)) / 2.0),  # 11: relative row grad
            torch.tanh(torch.log(m_row_norm / g_row_norm) / 2.0),              # 12: momentum/grad ratio
            _row_cos(G, M_cur),                                                # 13: cos(grad, mom)
            _row_cos(G, D_kfac_det),                                           # 14: cos(grad, K-FAC)
            e_rel,                                                             # 15: row error concentration
        ], dim=-1)                                                             # (d_out, 16)

        raw_ctrl, cap = forward_proposer_v2(phi, feats, capture_activations=(capture_self_acts is not None))
        if capture_self_acts is not None and cap is not None:
            capture_self_acts.append(cap)

        curv_mix = torch.sigmoid(raw_ctrl[:, 5:6])
        B_curv = curv_mix * B_kfac + (1.0 - curv_mix) * B_in_k
        mix_w = torch.tanh(raw_ctrl[:, 0:4])
        spec_w = torch.tanh(raw_ctrl[:, 8:9])
        D_comb = (
            mix_w[:, 0:1] * B_grad
            + mix_w[:, 1:2] * B_mom
            + mix_w[:, 2:3] * B_rms
            + mix_w[:, 3:4] * B_curv
            + spec_w * B_spec
        )
        # Unit-RMS normalize `D_comb` so unlocking K-FAC and Newton-Schulz rotates direction without inflating step norm!
        B_comb = norm_dir(D_comb)

        init_l_rms = float(opt_state["init_layer_rms"][l_idx])
        func_unit_scale = min(0.24, 1.0 / ((float(d_in1) ** 0.5) * float(act_rms.item()) + 1e-6))
        layer_scale = max(init_l_rms, func_unit_scale)
        eta = depth_trust * torch.sigmoid(raw_ctrl[:, 4:5]) * layer_scale
        gamma_base = 0.06 * torch.sigmoid(raw_ctrl[:, 6:7])
        gamma_head = (0.16 * torch.sigmoid(raw_ctrl[:, 7:8])) if is_head_f > 0.5 else 0.0
        gamma = gamma_base + gamma_head

        shrink_mask = torch.ones((1, d_in1), dtype=W.dtype, device=W.device)
        shrink_mask[0, -1] = 0.0
        W_reg_target = (W - proximal_anchors[l_idx]) if proximal_anchors is not None else W
        delta_W = -eta * B_comb - (gamma * shrink_mask) * W_reg_target

        step_rms = delta_W.detach().pow(2).mean().sqrt().clamp_min(1e-12)
        if float(step_rms.item()) > depth_trust:
            delta_W = delta_W * (depth_trust / step_rms)
        new_layers.append(W + delta_W)
    return new_layers


def self_modify_proposer_v2(
    parent_phi: ProposerWeightsV2,
    meta_loss: torch.Tensor,
    captured_forwards: list[dict[str, torch.Tensor]],
    self_opt_state: dict,
    meta_step_idx: int,
    total_meta_steps: int,
    trust_radius: float,
    proposer_rule_phi: ProposerWeightsV2 | None = None,
) -> ProposerWeightsV2:
    """Apply `proposer_rule_phi` (defaults to `parent_phi` for recursive self-application, or `Phi_0` for fixed-proposer control) to `{W_gate, W_up, W_out}`."""
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
        raw_updated = propose_update_v2(
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
            max_trust_step=0.31,
            differentiable_target=False,
            proximal_anchors=anchor_w,
        )
        deltas = [u - w.detach() for u, w in zip(raw_updated, w_list)]
        rms_all = float(torch.cat([d.reshape(-1) for d in deltas]).pow(2).mean().sqrt().clamp_min(1e-12).item())
        scale = min(1.0, float(trust_radius) / rms_all)
        updated = [w.detach() + scale * d for w, d in zip(w_list, deltas)]
    return ProposerWeightsV2.from_list(updated)
