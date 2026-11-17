"""Self-Applicable Multi-Layer SwiGLU Neural Weight-Proposer (`M_Phi`).

Architecture:
- `M_Phi` is a genuine 2-layer SwiGLU neural network with 3 weight+bias matrices:
  - `W_gate`: (H, F + 1)
  - `W_up`:   (H, F + 1)
  - `W_out`:  (O, H + 1)
  With `F = 14` scale-free equivariant structural inputs, `H = 32` SwiGLU hidden units, and `O = 7`
  outputs, `M_Phi` has `(32*15)*2 + (7*33) = 1,191` float64 neural parameters (or `H = 48` -> `1,783` params).
  We use `H = 48` (`1,783` float64 neural parameters).

Equivariant Neural Proposal Mechanism (NO hand-coded Barzilai-Borwein or secant formulas!):
- Given ANY multi-layer neural network target `{W_l}` (where each `W_l` in R^{d_out x (d_in + 1)} absorbs bias
  via homogeneous `1.0` input column — INCLUDING `M_Phi`'s OWN 3 matrices `{W_gate, W_up, W_out}`!),
  one forward-backward pass on a support batch `(X_sup, Y_sup)` produces for each layer `l`:
  - `A_{l-1}`: (N, d_in + 1) layer input activations
  - `E_l`:     (N, d_out) pre-activation loss gradients dL / dZ_l
  - `G_l`:     (d_out, d_in + 1) = E_l^T A_{l-1} / N
  - `Sigma_l`: (d_in + 1, d_in + 1) = A_{l-1}^T A_{l-1} / N (layer input activation covariance)
- `M_Phi` extracts 14 scale-free, neuron-permutation-equivariant structural features `f_{l, i}` for each
  output row `i` of layer `l` and outputs 7 neural controls:
  1..4: Combination logits/gates over 4 basis directions (`G_norm`, `Mom_norm`, `RMS_norm`, `Kron_natgrad`)
  5:    Log step-size gate `eta_{l, i}`
  6:    Layer input ridge-damping gate `lambda_{l}` for `(Sigma_l + lambda_l * tr_mean * I)^{-1}`
  7:    Anti-overfitting weight-shrinkage gate `gamma_{l, i}`

Self-Application (`M_Phi_g` modifies `Phi_g -> Phi_{g+1}`):
- During meta-improvement, `M_Phi_g` unrolls `B` adaptation steps on cold meta-training neural targets,
  evaluates held-out query loss `J_qry(Phi_g)`, backpropagates through the unrolled graph to obtain `M_Phi_g`'s
  own forward activations `(A_0^Phi, A_1^Phi)` and pre-activation meta-gradients `(E_gate^Phi, E_up^Phi, E_out^Phi)`,
  and invokes `propose_network_update(proposer=Phi_g, target_layers=Phi_g, ...)` — modifying ITS OWN weights
  without any external SGD/Adam optimizer!
"""
from __future__ import annotations

from dataclasses import dataclass
import torch
import torch.nn.functional as F

FEAT_DIM = 14
HID_DIM = 48
OUT_DIM = 7


@dataclass
class ProposerWeights:
    """Homogeneous weight matrices (bias in last column) so M_Phi has identical layer format to targets."""
    W_gate: torch.Tensor  # (48, 15)
    W_up: torch.Tensor    # (48, 15)
    W_out: torch.Tensor   # (7, 49)

    def as_list(self) -> list[torch.Tensor]:
        return [self.W_gate, self.W_up, self.W_out]

    @staticmethod
    def from_list(layers: list[torch.Tensor]) -> "ProposerWeights":
        assert len(layers) == 3
        return ProposerWeights(W_gate=layers[0], W_up=layers[1], W_out=layers[2])

    def clone_detached(self, requires_grad: bool = False) -> "ProposerWeights":
        return ProposerWeights(
            W_gate=self.W_gate.detach().clone().requires_grad_(requires_grad),
            W_up=self.W_up.detach().clone().requires_grad_(requires_grad),
            W_out=self.W_out.detach().clone().requires_grad_(requires_grad),
        )

    def num_parameters(self) -> int:
        return int(self.W_gate.numel() + self.W_up.numel() + self.W_out.numel())

    def to_flat_list(self) -> list[float]:
        return torch.cat([t.detach().reshape(-1) for t in self.as_list()]). double().tolist()

    @staticmethod
    def from_flat_list(vals: list[float], dtype: torch.dtype = torch.float64) -> "ProposerWeights":
        t = torch.tensor(vals, dtype=dtype)
        n1 = HID_DIM * (FEAT_DIM + 1)
        n2 = n1 + HID_DIM * (FEAT_DIM + 1)
        n3 = n2 + OUT_DIM * (HID_DIM + 1)
        assert t.numel() == n3, f"Expected {n3} params, got {t.numel()}"
        return ProposerWeights(
            W_gate=t[:n1].reshape(HID_DIM, FEAT_DIM + 1).clone(),
            W_up=t[n1:n2].reshape(HID_DIM, FEAT_DIM + 1).clone(),
            W_out=t[n2:n3].reshape(OUT_DIM, HID_DIM + 1).clone(),
        )


def init_gen0_proposer(seed: int = 202611, dtype: torch.dtype = torch.float64) -> ProposerWeights:
    """Initialize Generation-0 proposer `Phi_0` as an uncalibrated conservative neural updater.
    Small random weights around a plain conservative baseline (`eta ~ 0.025`, mostly raw gradient, weak preconditioning)
    with zero hand-tuned task priors.
    """
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    W_gate = 0.08 * torch.randn((HID_DIM, FEAT_DIM + 1), generator=gen, dtype=dtype)
    W_up = 0.08 * torch.randn((HID_DIM, FEAT_DIM + 1), generator=gen, dtype=dtype)
    W_out = 0.04 * torch.randn((OUT_DIM, HID_DIM + 1), generator=gen, dtype=dtype)
    # Bias column (last column) sets clean neutral initial operating point before self-improvement:
    # out[0..3]: basis weights (raw grad slightly positive, others near zero)
    # out[4]: step-size logit (-1.8 -> softplus ~ 0.03 conservative step)
    # out[5]: Kronecker damping logit (+0.8 -> high damping ~ 2.2 initially)
    # out[6]: shrinkage logit (-5.0 -> ~0 weight decay initially)
    W_out[0, -1] = 0.8
    W_out[1, -1] = 0.0
    W_out[2, -1] = 0.0
    W_out[3, -1] = -0.5
    W_out[4, -1] = -1.8
    W_out[5, -1] = 0.8
    W_out[6, -1] = -5.0
    return ProposerWeights(W_gate=W_gate, W_up=W_up, W_out=W_out)


def forward_proposer_net(
    phi: ProposerWeights,
    feats: torch.Tensor,
    capture_activations: bool = False,
) -> tuple[torch.Tensor, dict[str, torch.Tensor] | None]:
    """Forward `M_Phi` on row feature matrix `feats` (R, 14) -> `raw_ctrl` (R, 7).
    Optionally retains intermediate tensors `(A0_hom, Z_gate, Z_up, A1_hom, Z_out)` so `M_Phi`
    can inspect ITS OWN layer activations and pre-activation gradients during self-application!
    """
    ones0 = torch.ones((feats.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A0_hom = torch.cat([feats, ones0], dim=-1)                # (R, 15)
    Z_gate = A0_hom @ phi.W_gate.T                            # (R, 48)
    Z_up = A0_hom @ phi.W_up.T                                # (R, 48)
    H1 = F.silu(Z_gate) * Z_up                                # SwiGLU hidden activations (R, 48)
    ones1 = torch.ones((H1.shape[0], 1), dtype=feats.dtype, device=feats.device)
    A1_hom = torch.cat([H1, ones1], dim=-1)                   # (R, 49)
    Z_out = A1_hom @ phi.W_out.T                              # (R, 7)

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


def init_optimizer_state(layers: list[torch.Tensor]) -> dict[str, list[torch.Tensor] | float | None]:
    return {
        "mom": [torch.zeros_like(W.detach()) for W in layers],
        "rms": [torch.zeros_like(W.detach()) for W in layers],
        "loss0": None,
    }


def _row_cos(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    num = (a * b).sum(dim=-1)
    den = (a.pow(2).sum(dim=-1).sqrt() * b.pow(2).sum(dim=-1).sqrt()).clamp_min(1e-12)
    return (num / den).clamp(-1.0, 1.0)


def propose_network_update(
    phi: ProposerWeights,
    layers: list[torch.Tensor],
    grads: list[torch.Tensor],
    act_inputs: list[torch.Tensor],
    err_outputs: list[torch.Tensor],
    opt_state: dict,
    step_idx: int,
    total_steps: int,
    cur_loss: torch.Tensor,
    capture_self_acts: list[dict[str, torch.Tensor]] | None = None,
    max_trust_step: float = 0.65,
) -> list[torch.Tensor]:
    """Apply `M_Phi` to propose updated weight matrices `[W_l_next]` for ANY target neural network
    (including `M_Phi` itself during self-modification!). Differentiable wrt `phi` for meta-learning.
    """
    L = len(layers)
    loss_val = float(cur_loss.detach().item())
    if opt_state["loss0"] is None:
        opt_state["loss0"] = max(loss_val, 1e-8)
    loss0 = float(opt_state["loss0"])
    rel_loss = torch.tanh(torch.tensor((loss_val - loss0) / (loss0 + 1e-8), dtype=layers[0].dtype))

    new_layers: list[torch.Tensor] = []
    for l_idx in range(L):
        W = layers[l_idx]                                     # (d_out, d_in1)
        G = grads[l_idx].detach()                             # (d_out, d_in1)
        A = act_inputs[l_idx].detach()                        # (N, d_in1)
        E = err_outputs[l_idx].detach()                       # (N, d_out)
        d_out, d_in1 = W.shape
        N = max(1, A.shape[0])

        M_prev = opt_state["mom"][l_idx]
        V_prev = opt_state["rms"][l_idx]
        M_cur = 0.85 * M_prev + 0.15 * G
        V_cur = 0.90 * V_prev + 0.10 * (G * G)
        opt_state["mom"][l_idx] = M_cur.detach()
        opt_state["rms"][l_idx] = V_cur.detach()

        # Layer input covariance Sigma = (A^T A) / N in R^{d_in1 x d_in1}
        Sigma = (A.T @ A) / float(N)
        diag_s = Sigma.diagonal()
        tr_mean = diag_s.mean().clamp_min(1e-8)
        Sigma_norm = Sigma / tr_mean
        cond_proxy = torch.tanh(torch.log((diag_s.max() / (diag_s.mean() + 1e-8)).clamp_min(1.0)) / 4.0)

        # Preliminary Kronecker direction at canonical damping 0.25 to extract alignment features,
        # plus second Kronecker direction at tight damping 0.03 so M_Phi can smoothly interpolate curvature!
        eye_in = torch.eye(d_in1, dtype=W.dtype, device=W.device)
        D_kron_hi = torch.linalg.solve(Sigma_norm + 0.30 * eye_in, G.T).T
        D_kron_lo = torch.linalg.solve(Sigma_norm + 0.04 * eye_in, G.T).T

        # Normalize all candidate basis directions by layer RMS so step scale is cleanly controlled by M_Phi!
        def norm_dir(T_mat: torch.Tensor) -> torch.Tensor:
            rms = T_mat.pow(2).mean().sqrt().clamp_min(1e-10)
            return T_mat / rms

        B_grad = norm_dir(G)
        B_mom = norm_dir(M_cur)
        B_rms = norm_dir(G / (V_cur.sqrt() + 1e-8))
        B_k_hi = norm_dir(D_kron_hi)
        B_k_lo = norm_dir(D_kron_lo)

        # Construct 14 scale-free equivariant structural features per output row i in 0..d_out-1
        w_row_norm = W.detach().pow(2).mean(dim=-1).sqrt().clamp_min(1e-8)
        g_row_norm = G.pow(2).mean(dim=-1).sqrt().clamp_min(1e-12)
        m_row_norm = M_cur.pow(2).mean(dim=-1).sqrt().clamp_min(1e-12)
        e_row_rms = E.pow(2).mean(dim=0).sqrt()
        e_rel = (e_row_rms / e_row_rms.mean().clamp_min(1e-8)).clamp(0.0, 4.0) / 2.0 - 0.5

        depth_f = float(l_idx) / max(1.0, float(L - 1))
        step_f = float(step_idx) / max(1.0, float(total_steps - 1))
        fan_in_f = torch.log(torch.tensor(float(d_in1), dtype=W.dtype)) / 5.0
        fan_out_f = torch.log(torch.tensor(float(d_out), dtype=W.dtype)) / 5.0

        ones_r = torch.ones(d_out, dtype=W.dtype, device=W.device)
        feats = torch.stack([
            ones_r * depth_f,                                                  # 0: layer depth
            ones_r * step_f,                                                   # 1: adaptation step progress
            ones_r * (1.0 - step_f),                                           # 2: remaining budget
            ones_r * fan_in_f,                                                 # 3: log fan-in
            ones_r * fan_out_f,                                                # 4: log fan-out
            ones_r * rel_loss,                                                 # 5: relative loss ratio
            ones_r * cond_proxy,                                               # 6: activation conditioning
            torch.tanh(torch.log(g_row_norm / w_row_norm) / 4.0),              # 7: log grad/weight ratio
            torch.tanh(torch.log(g_row_norm / g_row_norm.mean().clamp_min(1e-12)) / 2.0),  # 8: relative row grad
            torch.tanh(torch.log(m_row_norm / g_row_norm) / 2.0),              # 9: momentum/grad ratio
            _row_cos(G, M_cur),                                                # 10: cos(grad, momentum)
            _row_cos(G, D_kron_lo),                                            # 11: cos(grad, Kronecker)
            _row_cos(M_cur, D_kron_lo),                                        # 12: cos(mom, Kronecker)
            e_rel,                                                             # 13: row error concentration
        ], dim=-1)                                                             # (d_out, 14)

        raw_ctrl, cap = forward_proposer_net(phi, feats, capture_activations=(capture_self_acts is not None))
        if capture_self_acts is not None and cap is not None:
            capture_self_acts.append(cap)

        # Decode the 7 neural outputs into bounded, stable update operators:
        # 0..3: softmax/tanh basis mix over (B_grad, B_mom, B_rms, B_kron_blend)
        kron_mix = torch.sigmoid(raw_ctrl[:, 5:6])                             # (d_out, 1): blends tight vs damped Kronecker!
        B_kron = kron_mix * B_k_lo + (1.0 - kron_mix) * B_k_hi
        mix_weights = torch.tanh(raw_ctrl[:, 0:4])                             # (d_out, 4) in [-1, 1]
        D_comb = (
            mix_weights[:, 0:1] * B_grad
            + mix_weights[:, 1:2] * B_mom
            + mix_weights[:, 2:3] * B_rms
            + mix_weights[:, 3:4] * B_kron
        )                                                                      # (d_out, d_in1)

        # Row step size eta in (0, max_trust_step) scaled gently by typical weight scale
        eta = max_trust_step * torch.sigmoid(raw_ctrl[:, 4:5]) * (0.25 + 0.75 * w_row_norm.unsqueeze(1).clamp(0.05, 2.0))
        # Row weight shrinkage regularizer gamma in (0, 0.08) (shrinks weights column-wise, excluding bias col!)
        gamma = 0.08 * torch.sigmoid(raw_ctrl[:, 6:7])
        shrink_mask = torch.ones((1, d_in1), dtype=W.dtype, device=W.device)
        shrink_mask[0, -1] = 0.0                                               # do not decay bias column

        delta_W = -eta * D_comb - (gamma * shrink_mask) * W
        # Safety trust clip on Frobenius step norm
        step_rms = delta_W.detach().pow(2).mean().sqrt().clamp_min(1e-12)
        if float(step_rms.item()) > max_trust_step:
            delta_W = delta_W * (max_trust_step / step_rms)

        new_layers.append(W + delta_W)
    return new_layers


def self_modify_proposer_step(
    parent_phi: ProposerWeights,
    meta_loss: torch.Tensor,
    captured_forwards: list[dict[str, torch.Tensor]],
    self_opt_state: dict,
    meta_step_idx: int,
    total_meta_steps: int,
) -> ProposerWeights:
    """SELF-APPLICATION CORE: Backpropagate `meta_loss` through `parent_phi`, assemble `parent_phi`'s
    OWN layer input activations `(A0, A0, A1)` and pre-activation meta-gradients `(E_gate, E_up, E_out)`,
    and call `propose_network_update(phi=parent_phi, layers=parent_phi, ...)` so `parent_phi` literally
    proposes the weight update to ITSELF!
    """
    w_list = parent_phi.as_list()
    grads = torch.autograd.grad(meta_loss, w_list, retain_graph=True, allow_unused=False)

    # Aggregate parent_phi's own forward activations and backward pre-activation error signals across unrolled calls!
    A0_all = torch.cat([c["A0_hom"] for c in captured_forwards], dim=0)        # (R_tot, 15)
    A1_all = torch.cat([c["A1_hom"] for c in captured_forwards], dim=0)        # (R_tot, 49)

    z_gates = [c["Z_gate"] for c in captured_forwards]
    z_ups = [c["Z_up"] for c in captured_forwards]
    z_outs = [c["Z_out"] for c in captured_forwards]
    e_All = torch.autograd.grad(meta_loss, z_gates + z_ups + z_outs, retain_graph=False, allow_unused=False)
    n_c = len(captured_forwards)
    E_gate_all = torch.cat(list(e_All[:n_c]), dim=0)                           # (R_tot, 48)
    E_up_all = torch.cat(list(e_All[n_c : 2 * n_c]), dim=0)                    # (R_tot, 48)
    E_out_all = torch.cat(list(e_All[2 * n_c :]), dim=0)                       # (R_tot, 7)

    # Subsample at most 512 rows for O(1) covariance computation while preserving exact weight gradients `grads`
    if A0_all.shape[0] > 512:
        stride = max(1, A0_all.shape[0] // 512)
        A0_all = A0_all[::stride][:512]
        A1_all = A1_all[::stride][:512]
        E_gate_all = E_gate_all[::stride][:512]
        E_up_all = E_up_all[::stride][:512]
        E_out_all = E_out_all[::stride][:512]

    with torch.no_grad():
        phi_frozen = parent_phi.clone_detached(requires_grad=False)
        cur_layers = [w.detach().clone() for w in w_list]
        updated_layers = propose_network_update(
            phi=phi_frozen,
            layers=cur_layers,
            grads=[g.detach() for g in grads],
            act_inputs=[A0_all.detach(), A0_all.detach(), A1_all.detach()],
            err_outputs=[E_gate_all.detach(), E_up_all.detach(), E_out_all.detach()],
            opt_state=self_opt_state,
            step_idx=meta_step_idx,
            total_steps=total_meta_steps,
            cur_loss=meta_loss.detach(),
            capture_self_acts=None,
            max_trust_step=0.18,
        )
    return ProposerWeights.from_list(updated_layers)
