"""Pure-PyTorch per-time-step reference for the three fla 0.5.1 components used
by pysrc/model.py KimiLinearAttention:

  1. chunk_kda(..., use_qk_l2norm_in_kernel=True, use_gate_in_kernel=True,
     cu_seqlens=...) -> kda_recurrent_reference
  2. FusedRMSNormGated(hidden_size=64, activation="sigmoid")
     -> fused_rmsnorm_gated_reference
  3. causal_conv1d(x, weight, activation="silu", cu_seqlens=...)
     -> causal_conv1d_silu_reference

Semantics extracted from the installed sources (see cpp_infer/KIMI_SEMANTICS.md
for the derivation and the validation results):
  - .venv/.../fla/ops/kda/fused_recurrent.py  (authoritative per-step form)
  - .venv/.../fla/ops/kda/{chunk,chunk_fwd,chunk_intra,gate,naive}.py
  - .venv/.../fla/ops/utils/softplus.py       (threshold-20 softplus)
  - .venv/.../fla/modules/l2norm.py           (eps 1e-6 inside sqrt of raw sum)
  - .venv/.../fla/modules/fused_norm_gate.py  (rmsnorm(x)*w*sigmoid(g), eps 1e-5)
  - .venv/.../fla/modules/conv/triton/kernels.py

Run the validation:
    .venv/bin/python pysrc/kda_reference.py            # default (tf32 dots in chunk path)
    .venv/bin/python pysrc/kda_reference.py --ieee     # forces TRITON_F32_DEFAULT=ieee
"""

from __future__ import annotations

import math
import os
import sys

import torch

# Exact constants used by the Triton kernels (fp32 literals in the kernels).
L2NORM_EPS = 1e-6            # added to the RAW sum of squares, inside sqrt
NORM_GATE_EPS = 1e-5         # added to the MEAN of squares, inside sqrt
SOFTPLUS_THRESHOLD = 20.0    # softplus(x) = x for x > 20, else log1p(exp(x))
# chunk_kda default scale for K=64 (model does not pass scale): K**-0.5
KDA_SCALE_K64 = 0.125


def kda_softplus(x: torch.Tensor) -> torch.Tensor:
    """softplus exactly as fla.ops.utils.softplus: where(x > 20, x, log(1+exp(x))).

    (The NVIDIA kernel evaluates the x<=20 branch with approximate PTX
    ex2.approx.ftz / lg2.approx.ftz; this reference uses exact log1p/exp.)
    """
    return torch.where(x > SOFTPLUS_THRESHOLD, x, torch.log1p(torch.exp(x)))


def kda_gate_reference(
    g_raw: torch.Tensor,   # [..., H, K] raw forget-gate pre-activation
    A_log: torch.Tensor,   # [H]
    dt_bias: torch.Tensor,  # [H*K] (viewed as [H, K])
) -> torch.Tensor:
    """Per-channel log-decay: g = -exp(A_log[h]) * softplus(g_raw + dt_bias[h])."""
    H, K = g_raw.shape[-2:]
    x = g_raw + dt_bias.view(H, K).to(g_raw.dtype)
    return -torch.exp(A_log.to(g_raw.dtype)).view(H, 1) * kda_softplus(x)


def l2norm_reference(x: torch.Tensor, eps: float = L2NORM_EPS) -> torch.Tensor:
    """y = x / sqrt(sum(x^2) + eps) over the last dim (eps added to the raw sum)."""
    return x / torch.sqrt(x.square().sum(-1, keepdim=True) + eps)


def kda_recurrent_reference(
    q: torch.Tensor,        # [1, T, H, K] fp32
    k: torch.Tensor,        # [1, T, H, K] fp32
    v: torch.Tensor,        # [1, T, H, V] fp32
    g_raw: torch.Tensor,    # [1, T, H, K] fp32 raw forget-gate pre-activation
    beta: torch.Tensor,     # [1, T, H]    fp32, already sigmoid()ed by the model
    A_log: torch.Tensor,    # [H] fp32
    dt_bias: torch.Tensor,  # [H*K] fp32
    cu_seqlens: torch.Tensor | None,  # [N+1] article boundaries; None = one article
    dtype: torch.dtype = torch.float64,   # accumulation/compute dtype
    scale: float | None = None,           # None -> K**-0.5 (chunk_kda default)
) -> torch.Tensor:
    """Exact per-time-step recurrent form of chunk_kda as called by model.py.

    Per head h, per article, with state S in R^{K x V} initialized to 0:
        qn   = q_t / sqrt(sum(q_t^2) + 1e-6)
        kn   = k_t / sqrt(sum(k_t^2) + 1e-6)
        g    = -exp(A_log[h]) * softplus(g_raw_t + dt_bias[h])        # [K], <= 0
        S    = diag(exp(g)) @ S            # decay each k-row, BEFORE delta rule
        r    = S^T kn                      # [V], uses the DECAYED state
        u    = beta_t[h] * (v_t - r)       # [V]
        S    = S + outer(kn, u)            # S[i,j] += kn[i] * u[j]
        o_t  = S^T (scale * qn)            # [V], scale = K**-0.5 = 0.125
    Returns o of shape [1, T, H, V] in `dtype`.
    """
    assert q.dim() == 4 and q.shape[0] == 1
    B, T, H, K = q.shape
    V = v.shape[-1]
    if scale is None:
        scale = K ** -0.5

    dev = q.device
    qf = q[0].to(dtype)
    kf = k[0].to(dtype)
    vf = v[0].to(dtype)
    bf = beta[0].to(dtype)
    # Precompute the per-channel log-decay for all positions at once (elementwise).
    gate = kda_gate_reference(g_raw[0].to(dtype), A_log.to(dtype), dt_bias.to(dtype))
    decay = torch.exp(gate)                     # [T, H, K]
    qn = l2norm_reference(qf) * scale           # [T, H, K]
    kn = l2norm_reference(kf)                   # [T, H, K]

    if cu_seqlens is None:
        bounds = [0, T]
    else:
        bounds = [int(x) for x in cu_seqlens.tolist()]
        assert bounds[0] == 0 and bounds[-1] == T

    o = torch.empty(T, H, V, dtype=dtype, device=dev)
    for a in range(len(bounds) - 1):
        S = torch.zeros(H, K, V, dtype=dtype, device=dev)
        for t in range(bounds[a], bounds[a + 1]):
            S = S * decay[t].unsqueeze(-1)                     # [H,K,1] * [H,K,V]
            r = (kn[t].unsqueeze(-1) * S).sum(-2)              # [H,V] = k^T S
            u = bf[t].unsqueeze(-1) * (vf[t] - r)              # [H,V]
            S = S + kn[t].unsqueeze(-1) * u.unsqueeze(-2)      # outer(kn, u)
            o[t] = (qn[t].unsqueeze(-1) * S).sum(-2)           # [H,V] = S^T q
    return o.unsqueeze(0)


def fused_rmsnorm_gated_reference(
    x: torch.Tensor,       # [..., D] kda output (per-head vectors)
    gate: torch.Tensor,    # [..., D] output-gate pre-activation
    weight: torch.Tensor,  # [D]
    eps: float = NORM_GATE_EPS,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """FusedRMSNormGated(activation="sigmoid"):
    y = (x / sqrt(mean(x^2) + 1e-5)) * weight * sigmoid(gate)
    (norm over the last dim D=64, i.e. per head; gate applied AFTER norm*weight).
    """
    xf = x.to(dtype)
    var = xf.square().sum(-1, keepdim=True) / x.shape[-1]
    rstd = 1.0 / torch.sqrt(var + eps)
    y = xf * rstd * weight.to(dtype)
    return y * torch.sigmoid(gate.to(dtype))


def causal_conv1d_silu_reference(
    x: torch.Tensor,       # [1, T, D] fp32
    weight: torch.Tensor,  # [D, W]
    cu_seqlens: torch.Tensor | None,
    dtype: torch.dtype = torch.float32,
) -> torch.Tensor:
    """causal_conv1d(activation='silu', no bias):
    y[t, c] = silu( sum_{j=0..W-1} weight[c, j] * x[t-(W-1)+j, c] )
    with x = 0 before each article start (weight[:, W-1] multiplies the NEWEST
    sample, weight[:, 0] the oldest); silu(z) = z * sigmoid(z).
    """
    assert x.dim() == 3 and x.shape[0] == 1
    T, D = x.shape[1], x.shape[2]
    W = weight.shape[-1]
    xf = x[0].to(dtype)
    wf = weight.to(dtype)
    if cu_seqlens is None:
        bounds = [0, T]
    else:
        bounds = [int(b) for b in cu_seqlens.tolist()]
    y = torch.zeros(T, D, dtype=dtype, device=x.device)
    for a in range(len(bounds) - 1):
        s, e = bounds[a], bounds[a + 1]
        seg = xf[s:e]                                    # [L, D]
        acc = torch.zeros_like(seg)
        for j in range(W):                               # ascending j like the kernel
            shift = W - 1 - j                            # input offset t - shift
            if shift == 0:
                acc = acc + wf[:, j] * seg
            else:
                acc[shift:] = acc[shift:] + wf[:, j] * seg[:-shift]
        y[s:e] = acc * torch.sigmoid(acc)
    return y.unsqueeze(0)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _err(name: str, out: torch.Tensor, ref: torch.Tensor, floor: float = 1e-3):
    a = out.double().flatten()
    b = ref.double().flatten()
    d = (a - b).abs()
    maxabs = d.max().item()
    rel = (d / b.abs().clamp_min(floor)).max().item()
    big = b.abs() > 1e-2
    relbig = (d[big] / b[big].abs()).max().item() if big.any() else float("nan")
    rms = b.square().mean().sqrt().item()
    print(
        f"  {name:44s} max|d|={maxabs:9.3e}  max rel(floor {floor:g})={rel:9.3e}  "
        f"max rel(|ref|>1e-2)={relbig:9.3e}  rms(ref)={rms:8.3e}"
    )
    return maxabs, rel


def _load_ckpt_gate_params(device):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "models", "6m-q4-fp32.tch")
    try:
        sd = torch.load(path, map_location="cpu", weights_only=False)
        if not isinstance(sd, dict):
            sd = sd.state_dict()
        A_log = sd["blocks.0.attention.log_baseline_decay_rate"].float().to(device)
        dt_bias = sd["blocks.0.attention.dt_bias"].float().to(device)
        print(f"loaded A_log/dt_bias from checkpoint: exp(A_log)={A_log.exp().tolist()}, "
              f"dt_bias in [{dt_bias.min().item():.4f}, {dt_bias.max().item():.4f}]")
        return A_log, dt_bias
    except Exception as exc:  # noqa: BLE001
        print(f"checkpoint not available ({exc}); using synthetic A_log/dt_bias")
        g = torch.Generator(device="cpu").manual_seed(7)
        A_log = torch.empty(3).uniform_(1, 16, generator=g).log().to(device)
        dt = torch.rand(192, generator=g) * (math.log(0.1) - math.log(0.001)) + math.log(0.001)
        dt = dt.exp().clamp(min=1e-4)
        dt_bias = (dt + torch.log(-torch.expm1(-dt))).to(device)
        return A_log, dt_bias


def _validate(device: torch.device):
    from fla.modules import FusedRMSNormGated
    from fla.modules.conv.causal_conv1d import causal_conv1d
    from fla.ops.kda import chunk_kda
    from fla.ops.kda.fused_recurrent import fused_recurrent_kda

    torch.manual_seed(1234)
    T, H, K, V, D, W = 4096, 3, 64, 64, 192, 4
    cu = torch.tensor([0, 1500, 1501, 4096], dtype=torch.long, device=device)

    # Realistic scales: q,k,v ~ post-conv+silu; g_raw ~ N(0, sqrt(2)); beta = sigmoid(N(0,1)).
    def mk(shape):
        return torch.randn(*shape, device=device)

    q = torch.nn.functional.silu(mk((1, T, H, K))).contiguous()
    k = torch.nn.functional.silu(mk((1, T, H, K))).contiguous()
    v = torch.nn.functional.silu(mk((1, T, H, V))).contiguous()
    g_raw = (mk((1, T, H, K)) * math.sqrt(2.0)).contiguous()
    beta = torch.sigmoid(mk((1, T, H))).contiguous()
    A_log, dt_bias = _load_ckpt_gate_params(device)

    print("\n== chunk_kda (fp32 triton) vs per-step recurrent reference ==")
    o_chunk, _ = chunk_kda(
        q=q, k=k, v=v, g=g_raw, beta=beta,
        A_log=A_log, dt_bias=dt_bias,
        use_qk_l2norm_in_kernel=True, use_gate_in_kernel=True,
        cu_seqlens=cu,
    )
    o_rec, _ = fused_recurrent_kda(
        q=q, k=k, v=v, g=g_raw, beta=beta,
        A_log=A_log, dt_bias=dt_bias,
        use_qk_l2norm_in_kernel=True, use_gate_in_kernel=True,
        cu_seqlens=cu,
    )
    ref64 = kda_recurrent_reference(q, k, v, g_raw, beta, A_log, dt_bias, cu,
                                    dtype=torch.float64)
    ref32 = kda_recurrent_reference(q, k, v, g_raw, beta, A_log, dt_bias, cu,
                                    dtype=torch.float32)
    _err("chunk_kda vs ref fp64", o_chunk, ref64)
    _err("chunk_kda vs ref fp32", o_chunk, ref32)
    _err("fused_recurrent_kda vs ref fp64", o_rec, ref64)
    _err("fused_recurrent_kda vs ref fp32", o_rec, ref32)
    _err("chunk_kda vs fused_recurrent_kda", o_chunk, o_rec)
    _err("ref fp32 vs ref fp64", ref32, ref64)

    # Length-1 article sanity: article 1 is [1500, 1501).
    t0 = 1500
    with torch.no_grad():
        qn = l2norm_reference(q[0, t0].double()) * KDA_SCALE_K64
        kn = l2norm_reference(k[0, t0].double())
        u = beta[0, t0, :, None].double() * v[0, t0].double()
        o_manual = (qn * kn).sum(-1, keepdim=True) * u
    d = (o_manual - o_chunk[0, t0].double()).abs().max().item()
    print(f"  length-1 article closed form vs chunk_kda: max|d|={d:.3e}")

    print("\n== FusedRMSNormGated(64, activation='sigmoid') ==")
    m = FusedRMSNormGated(hidden_size=64, activation="sigmoid").to(device).float()
    with torch.no_grad():
        m.weight.copy_(torch.randn(64, device=device) * 0.5 + 1.0)
    x = mk((1, T, H, 64))
    gate = mk((1, T, H, 64)) * 2
    with torch.no_grad():
        y = m(x, gate)
    y64 = fused_rmsnorm_gated_reference(x, gate, m.weight, dtype=torch.float64)
    y32 = fused_rmsnorm_gated_reference(x, gate, m.weight, dtype=torch.float32)
    _err("module vs ref fp64", y, y64)
    _err("module vs ref fp32", y, y32)

    print("\n== causal_conv1d (silu, cu_seqlens) ==")
    xc = mk((1, T, D))
    wc = mk((D, W)) * 0.5
    with torch.no_grad():
        yc, _ = causal_conv1d(x=xc, weight=wc, activation="silu", cu_seqlens=cu)
    yc64 = causal_conv1d_silu_reference(xc, wc, cu, dtype=torch.float64)
    yc32 = causal_conv1d_silu_reference(xc, wc, cu, dtype=torch.float32)
    _err("module vs ref fp64", yc, yc64)
    _err("module vs ref fp32", yc, yc32)


if __name__ == "__main__":
    if "--ieee" in sys.argv:
        os.environ["TRITON_F32_DEFAULT"] = "ieee"
        print("TRITON_F32_DEFAULT=ieee (tl.dot on fp32 uses full IEEE fp32)")
    else:
        print("TRITON_F32_DEFAULT unset (tl.dot on fp32 defaults to tf32 on sm80+)")
    assert torch.cuda.is_available(), "validation requires the GPU triton kernels"
    _validate(torch.device("cuda"))
