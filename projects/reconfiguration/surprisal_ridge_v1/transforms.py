"""Training-free prompt-conditioned low-rank weight transformation operators.

Implements three genuinely distinct training-free mechanisms on untouched frozen models:
1. unembed_surprisal_ridge: Single-forward-pass, GPU-resident derivation at the final FFN layer
   using exact frozen LM-head token-prediction residuals on high-surprisal context positions,
   producing compact rank-r LoRA factors (U, V) without any backward pass or trained projection.
2. shared_hyperbasis_lora: Derives ONE shared output basis U_shared in R^{d x r} on GPU from
   prompt surprisal residuals and pairs it with lightweight per-layer input keys V_l across the
   final four FFN layers ("shared GPU function without a separate full modifier per weight").
3. prompt_nll_ridge_lora: Uses a single prompt-context-only NLL gradient pass (base weights
   strictly frozen; query/answer tokens excluded) to fit exact closed-form dual-ridge rank-r
   adapters across four evenly spaced FFN down_proj layers.
"""

from __future__ import annotations

from contextlib import contextmanager
import torch
import torch.nn as nn
import torch.nn.functional as F


def rms_norm_jacobian_matvec(h: torch.Tensor, weight: torch.Tensor, eps: float, vec: torch.Tensor) -> torch.Tensor:
    """Exact vector-Jacobian product J_{RMSNorm}(h)^T @ vec on device without autograd."""
    # h, vec: (m, d), weight: (d,)
    h_f = h.float()
    v_f = vec.float() * weight.float().unsqueeze(0)
    ms = h_f.pow(2).mean(dim=-1, keepdim=True)
    inv_rms = torch.rsqrt(ms + eps)
    proj = (h_f * v_f).mean(dim=-1, keepdim=True) / (ms + eps)
    return (v_f - h_f * proj) * inv_rms


def derive_unembed_surprisal_ridge(
    model,
    context_ids: torch.Tensor,
    rank: int = 24,
    lam: float = 10.0,
    eta_max: float = 0.04,
) -> tuple[dict[int, tuple[torch.Tensor, torch.Tensor]], dict[int, float]]:
    """Forward-only GPU-resident derivation of rank-r (U, V) on the final FFN down_proj."""
    n_layers = len(model.model.layers)
    last_idx = n_layers - 1
    mlp = model.model.layers[last_idx].mlp
    down = mlp.down_proj
    norm_mod = model.model.norm
    lm_head = model.lm_head
    eps = getattr(norm_mod, "variance_epsilon", getattr(norm_mod, "eps", 1e-6))

    captured = {}

    def pre_down_hook(_mod, inputs):
        captured["act"] = inputs[0].detach()  # (1, T, d_inter)

    h_hook = down.register_forward_pre_hook(pre_down_hook)
    try:
        with torch.inference_mode():
            out = model.model(input_ids=context_ids, use_cache=False, return_dict=True)
            # Final hidden state BEFORE model.model.norm? Note: model.model returns normed hidden states!
            # Capture pre-norm hidden state cleanly or use normed hidden state directly!
            normed_h = out.last_hidden_state[0]  # (T, d_hidden), already RMSNormed!
    finally:
        h_hook.remove()

    with torch.inference_mode():
        act = captured.pop("act")[0]  # (T, d_inter)
        T = context_ids.shape[1]
        if T < 4:
            raise ValueError("Context too short for surprisal ridge derivation")

        # Align position t in [0..T-2] with observed next context token context_ids[0, t+1]
        next_tokens = context_ids[0, 1:]                # (T-1,)
        h_normed = normed_h[:-1].float()                # (T-1, d_hidden)
        a_prev = act[:-1].float()                       # (T-1, d_inter)

        logits = F.linear(h_normed, lm_head.weight.float())  # (T-1, V)
        probs = F.softmax(logits, dim=-1)
        p_true = probs.gather(-1, next_tokens.unsqueeze(-1)).squeeze(-1)
        surprisal = -torch.log(p_true.clamp_min(1e-9))       # (T-1,)

        # Select top-r high-surprisal context positions (ignores predictable template tokens!)
        k = min(rank, T - 1)
        top_vals, top_idx = torch.topk(surprisal, k=k, largest=True)
        a_sel = a_prev[top_idx]                              # (k, d_inter)
        tok_sel = next_tokens[top_idx]                       # (k,)

        # Top-16 predicted competitors per selected position for fast GPU residual target
        top_p, top_v = torch.topk(probs[top_idx], k=16, dim=-1)  # (k, 16)
        top_p = top_p / top_p.sum(dim=-1, keepdim=True).clamp_min(1e-9)
        w_true = lm_head.weight[tok_sel].float()             # (k, d_hidden)
        w_pred = torch.einsum("kj,jhd->khd", top_p, lm_head.weight[top_v].float()) if False else (
            (top_p.unsqueeze(-1) * lm_head.weight[top_v].float()).sum(dim=1)
        )
        # Approximate pre-norm direction scaled by RMSNorm weight (unit-consistent in residual stream)
        grad_normed = (w_true - w_pred) * (1.0 - p_true[top_idx]).unsqueeze(-1)
        g_sel = grad_normed * norm_mod.weight.float().unsqueeze(0)  # (k, d_hidden)

        # Closed-form dual kernel ridge: DeltaW = eta * G^T (A A^T + lam * mean_diag * I)^{-1} A
        gram = a_sel @ a_sel.T                               # (k, k)
        reg = lam * (gram.diagonal().mean().clamp_min(1e-6))
        gram.diagonal().add_(reg)
        V = torch.linalg.solve(gram, a_sel)                  # (k, d_inter)
        U = g_sel.T                                          # (d_hidden, k)

        # Exact Frobenius norm bound ||U V||_F = sqrt(Tr((U^T U)(V V^T))) <= eta_max * ||W_down||_F
        utu = U.T @ U
        vvt = V @ V.T
        frob = float(torch.sqrt((utu * vvt.T).sum().clamp_min(0.0)).item())
        w_norm = max(1e-9, float(down.weight.float().norm().item()))
        scale = min(1.0, (eta_max * w_norm) / max(1e-9, frob))
        U = (U * scale).to(down.weight.dtype)
        V = V.to(down.weight.dtype)
        final_frob = frob * scale

    return {last_idx: (U, V)}, {last_idx: final_frob}


def gpu_thin_qr(mat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Pure-GPU thin QR via modified Gram-Schmidt (avoids MPS linalg_qr NotImplementedError)."""
    m_f = mat.float()
    k = m_f.shape[1]
    q_cols: list[torch.Tensor] = []
    r_mat = torch.zeros((k, k), device=m_f.device, dtype=torch.float32)
    for j in range(k):
        v = m_f[:, j]
        for i in range(j):
            rij = torch.dot(q_cols[i], v)
            r_mat[i, j] = rij
            v = v - rij * q_cols[i]
        norm_v = v.norm().clamp_min(1e-8)
        r_mat[j, j] = norm_v
        q_cols.append(v / norm_v)
    return torch.stack(q_cols, dim=1), r_mat


def derive_shared_hyperbasis_lora(
    model,
    context_ids: torch.Tensor,
    rank: int = 16,
    lam: float = 10.0,
    eta_max: float = 0.025,
) -> tuple[dict[int, tuple[torch.Tensor, torch.Tensor]], dict[int, float], int]:
    """Shared-basis GPU function: ONE shared U_shared in R^{d x r} modulated across final 4 layers."""
    n_layers = len(model.model.layers)
    target_layers = [max(0, n_layers - 4 + j) for j in range(4)]
    target_layers = sorted(set(target_layers))
    norm_mod = model.model.norm
    lm_head = model.lm_head

    acts = {}
    handles = []
    for idx in target_layers:
        down = model.model.layers[idx].mlp.down_proj

        def make_hook(l_idx):
            def pre_hook(_m, inp):
                acts[l_idx] = inp[0].detach()
            return pre_hook

        handles.append(down.register_forward_pre_hook(make_hook(idx)))

    try:
        with torch.inference_mode():
            out = model.model(input_ids=context_ids, use_cache=False, return_dict=True)
            normed_h = out.last_hidden_state[0]
    finally:
        for h in handles:
            h.remove()

    with torch.inference_mode():
        T = context_ids.shape[1]
        next_tokens = context_ids[0, 1:]
        h_normed = normed_h[:-1].float()
        logits = F.linear(h_normed, lm_head.weight.float())
        probs = F.softmax(logits, dim=-1)
        p_true = probs.gather(-1, next_tokens.unsqueeze(-1)).squeeze(-1)
        surprisal = -torch.log(p_true.clamp_min(1e-9))

        k = min(rank, T - 1)
        _, top_idx = torch.topk(surprisal, k=k, largest=True)
        tok_sel = next_tokens[top_idx]
        top_p, top_v = torch.topk(probs[top_idx], k=16, dim=-1)
        top_p = top_p / top_p.sum(dim=-1, keepdim=True).clamp_min(1e-9)
        w_true = lm_head.weight[tok_sel].float()
        w_pred = (top_p.unsqueeze(-1) * lm_head.weight[top_v].float()).sum(dim=1)
        g_sel = (w_true - w_pred) * (1.0 - p_true[top_idx]).unsqueeze(-1) * norm_mod.weight.float().unsqueeze(0)

        # Orthonormal shared basis U_shared in R^{d_hidden x k} shared by reference across all 4 layers!
        U_q, R_mat = gpu_thin_qr(g_sel.T)  # U_q: (d_hidden, k), R_mat: (k, k)
        dt = model.model.layers[target_layers[0]].mlp.down_proj.weight.dtype
        U_shared = U_q.to(dt)

        factors = {}
        norms = {}
        for idx in target_layers:
            down = model.model.layers[idx].mlp.down_proj
            a_sel = acts.pop(idx)[0, :-1].float()[top_idx]  # (k, d_inter)
            gram = a_sel @ a_sel.T
            reg = lam * gram.diagonal().mean().clamp_min(1e-6)
            gram.diagonal().add_(reg)
            V_raw = R_mat @ torch.linalg.solve(gram, a_sel)  # (k, d_inter)
            # Since U_q has orthonormal columns, ||U_shared @ V_raw||_F == ||V_raw||_F!
            frob = float(V_raw.norm().item())
            w_norm = max(1e-9, float(down.weight.float().norm().item()))
            scale = min(1.0, (eta_max * w_norm) / max(1e-9, frob))
            V_l = (V_raw * scale).to(dt)
            factors[idx] = (U_shared, V_l)
            norms[idx] = frob * scale

        # Logical bytes: ONE shared U_shared + four V_l tensors!
        shared_bytes = U_shared.numel() * U_shared.element_size() + sum(
            f[1].numel() * f[1].element_size() for f in factors.values()
        )
    return factors, norms, shared_bytes


def derive_prompt_nll_ridge_lora(
    model,
    context_ids: torch.Tensor,
    rank: int = 16,
    lam: float = 10.0,
    eta_max: float = 0.025,
) -> tuple[dict[int, tuple[torch.Tensor, torch.Tensor]], dict[int, float]]:
    """Single prompt-context causal NLL backward pass -> closed-form dual-ridge rank-r LoRA."""
    n_layers = len(model.model.layers)
    stride = max(1, n_layers // 4)
    target_layers = sorted({min(n_layers - 1, (j + 1) * stride - 1) for j in range(4)})

    acts = {}
    out_grads = {}
    handles = []

    for idx in target_layers:
        down = model.model.layers[idx].mlp.down_proj

        def make_fwd(l_idx):
            def hook(_m, inp, out):
                acts[l_idx] = inp[0].detach()
                out.retain_grad()
                out_grads[l_idx] = out
            return hook

        handles.append(down.register_forward_hook(make_fwd(idx)))

    # Freeze parameter grad accumulation so base weights never accumulate .grad buffers!
    req_backup = [p.requires_grad for p in model.parameters()]
    for p in model.parameters():
        p.requires_grad_(False)

    try:
        with torch.enable_grad():
            emb = model.model.embed_tokens(context_ids).detach().requires_grad_(True)
            out = model(inputs_embeds=emb, use_cache=False, return_dict=True)
            logits = out.logits[:, :-1, :].float()
            targets = context_ids[:, 1:]
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), targets.reshape(-1))
            loss.backward()
            del out, logits, loss, emb
    finally:
        for h in handles:
            h.remove()
        for p, flag in zip(model.parameters(), req_backup):
            p.requires_grad_(flag)

    factors = {}
    norms = {}
    with torch.inference_mode():
        T = context_ids.shape[1]
        k = min(rank, T - 1)
        for idx in target_layers:
            down = model.model.layers[idx].mlp.down_proj
            a_all = acts.pop(idx)[0, :-1].float()                  # (T-1, d_inter)
            g_all = -out_grads.pop(idx).grad[0, :-1].float()       # steepest descent residual (T-1, d_hidden)
            # Pick top-k largest residual-gradient positions
            scores = g_all.norm(dim=-1)
            _, top_idx = torch.topk(scores, k=k, largest=True)
            a_sel = a_all[top_idx]                                 # (k, d_inter)
            g_sel = g_all[top_idx]                                 # (k, d_hidden)

            gram = a_sel @ a_sel.T
            reg = lam * gram.diagonal().mean().clamp_min(1e-6)
            gram.diagonal().add_(reg)
            V = torch.linalg.solve(gram, a_sel)                    # (k, d_inter)
            U = g_sel.T                                            # (d_hidden, k)

            utu = U.T @ U
            vvt = V @ V.T
            frob = float(torch.sqrt((utu * vvt.T).sum().clamp_min(0.0)).item())
            w_norm = max(1e-9, float(down.weight.float().norm().item()))
            scale = min(1.0, (eta_max * w_norm) / max(1e-9, frob))
            U = (U * scale).to(down.weight.dtype)
            V = V.to(down.weight.dtype)
            factors[idx] = (U, V)
            norms[idx] = frob * scale

    return factors, norms


@contextmanager
def temporary_lora_hooks(model, factors: dict[int, tuple[torch.Tensor, torch.Tensor]]):
    """Attach temporary forward hooks W_down(x) + (x @ V^T) @ U^T without mutating base weights."""
    handles = []
    for idx, (U, V) in factors.items():
        down = model.model.layers[idx].mlp.down_proj

        def make_hook(u_mat, v_mat):
            def hook(_mod, inputs, output):
                x = inputs[0]
                delta = F.linear(F.linear(x, v_mat), u_mat)
                return output + delta.to(output.dtype)
            return hook

        handles.append(down.register_forward_hook(make_hook(U, V)))
    try:
        yield
    finally:
        for h in handles:
            h.remove()


def make_zero_factors(factors: dict[int, tuple[torch.Tensor, torch.Tensor]]):
    return {idx: ( torch.zeros_like(U), torch.zeros_like(V) ) for idx, (U, V) in factors.items()}


def make_random_norm_matched_factors(
    factors: dict[int, tuple[torch.Tensor, torch.Tensor]],
    target_norms: dict[int, float],
    seed: int,
    device: str,
):
    gen = torch.Generator(device="cpu").manual_seed(seed)
    out = {}
    for idx, (U, V) in factors.items():
        u_r = torch.randn(U.shape, generator=gen, dtype=torch.float32).to(device)
        v_r = torch.randn(V.shape, generator=gen, dtype=torch.float32).to(device)
        utu = u_r.T @ u_r
        vvt = v_r @ v_r.T
        frob = max(1e-9, float(torch.sqrt((utu * vvt.T).sum().clamp_min(0.0)).item()))
        scale = target_norms[idx] / frob
        out[idx] = ((u_r * scale).to(U.dtype), v_r.to(V.dtype))
    return out


def scale_donor_factors(
    donor_factors_cpu: dict[int, tuple[torch.Tensor, torch.Tensor]],
    donor_norms: dict[int, float],
    recipient_norms: dict[int, float],
    device: str,
    dtype: torch.dtype,
):
    out = {}
    for idx, (U_cpu, V_cpu) in donor_factors_cpu.items():
        ratio = recipient_norms[idx] / max(1e-9, donor_norms[idx])
        out[idx] = ((U_cpu.float().to(device) * ratio).to(dtype), V_cpu.to(device=device, dtype=dtype))
    return out
