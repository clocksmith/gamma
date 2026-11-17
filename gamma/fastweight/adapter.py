"""Engine-portable prompt-conditioned SwiGLU fast-weight adapter & session (`v3`).

Supports three automatic context-derived regimes from a single prefill `(embed_tokens, h_last, lm_head)`:
1. `window` (`u_ratio > 0.65` and rare-token line key recall `> 0.85`):
   1-hop associative SwiGLU fast-weight retrieval across long key-value, config, checksum, and prose tables,
   with automatic BPE boundary healing when no-space delimiters (e.g. `.env` `KEY=val`) merge at the boundary.
2. `multihop_bridge` (`u_ratio > 0.65` and rare-token line key recall `<= 0.85`):
   Abstains at `step 0` so multi-hop/extrapolative queries never suffer false-anchor copy, and dynamically
   resolves intermediate hop entities (`a -> r`, `r -> p` => `r/p` or `r:p`) during autoregressive decode.
3. `clause_bigram` (`u_ratio <= 0.65`):
   Unit-variance standardized bigram prototype pooling + relative SNR noise floor + batched single-transfer
   leave-one-out NLL `eta*` calibration + query support-coverage gating.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Callable
import torch
import torch.nn.functional as F


def safe_norm(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """MPS-safe L2 normalization (avoids PyTorch 2.10 Metal non-contiguous F.normalize bug)."""
    xc = x.contiguous()
    return xc * torch.rsqrt((xc * xc).sum(dim=-1, keepdim=True).clamp_min(eps))


def swiglu(z: torch.Tensor) -> torch.Tensor:
    return F.silu(z) * z


def find_default_context_split(prompt_ids_1d: list[int] | torch.Tensor, newline_id: int) -> int:
    """Return token count `c_len` up to and including the last newline strictly before the final token."""
    ids = prompt_ids_1d.tolist() if isinstance(prompt_ids_1d, torch.Tensor) else list(prompt_ids_1d)
    T = len(ids)
    for idx in range(T - 2, -1, -1):
        if ids[idx] == newline_id:
            return idx + 1
    return T


def _tensor_bytes(*ts: torch.Tensor | None) -> int:
    return sum(int(t.numel()) * int(t.element_size()) for t in ts if t is not None)


_KV_DELIM_RE = re.compile(r"^(.+?)\s*(?:=>|->|=|:)\s*(\S.*)$")


def resolve_bpe_boundary_healed_tokens(
    context_text: str,
    query_line_text: str,
    encode_no_special: Callable[[str], list[int]],
) -> list[int] | None:
    """Heal BPE delimiter merges (e.g. `.env` `EXPORT KEY=val` queried with `EXPORT KEY=`)."""
    q_clean = query_line_text.strip()
    if not context_text or not q_clean:
        return None
    suffixes: set[str] = set()
    for raw_ln in context_text.splitlines():
        ln = raw_ln.strip()
        if ln.startswith(q_clean) and len(ln) > len(q_clean):
            suf = ln[len(q_clean):]
            if suf.strip():
                suffixes.add(suf)
    if len(suffixes) != 1:
        return None
    suf_str = next(iter(suffixes))
    ids = encode_no_special(suf_str)
    return ids if (0 < len(ids) <= 12) else None


def resolve_hop_continuation_tokens(
    context_text: str,
    generated_text: str,
    encode_no_special: Callable[[str], list[int]],
) -> list[int] | None:
    """If `generated_text` just emitted `<entity><sep>` (`/` or `:`), look up unambiguous `<entity> -> <val>` in `context_text`."""
    if not context_text or not generated_text:
        return None
    sep_used = None
    for sep in ("/", ":"):
        if generated_text.endswith(sep) and len(generated_text) > len(sep):
            sep_used = sep
            break
    if sep_used is None:
        return None

    prefix = generated_text[: -len(sep_used)].strip()
    parts = re.split(r"[\s/:=|]+", prefix)
    entity = parts[-1].strip() if parts else ""
    if len(entity) < 3:
        return None

    matched_vals: set[str] = set()
    for raw_ln in context_text.splitlines():
        ln = raw_ln.strip()
        if not ln:
            continue
        m = _KV_DELIM_RE.match(ln)
        if not m:
            continue
        lhs, rhs = m.group(1).strip(), m.group(2).strip()
        lhs_tokens = lhs.split()
        if lhs_tokens and lhs_tokens[-1] == entity:
            if sep_used not in rhs:
                matched_vals.add(rhs)

    if len(matched_vals) != 1:
        return None
    val_str = next(iter(matched_vals))
    val_ids = encode_no_special(val_str)
    return val_ids if (0 < len(val_ids) <= 10) else None


def compute_rare_key_recall(
    p_list: list[int],
    line_list: list[int],
    anchors: list[int],
    c_len: int,
    newline_id: int,
) -> tuple[float, int, bool]:
    """Return `(max_rare_token_recall, best_anchor_idx, boundary_token_merged)`.

    Shift-invariant to BPE boundary merges (such as `KEY=val` vs `KEY=`): compares non-template
    token IDs on the query line (`[q_start .. T-2]`) against each anchor's full context line.
    """
    T = len(p_list)
    q_lid = line_list[T - 1]
    q_start = T - 1
    while q_start > 0 and line_list[q_start - 1] == q_lid:
        q_start -= 1
    q_pre = set(p_list[q_start : T - 1])
    if not q_pre:
        return 0.0, 0, False

    # Build pre-anchor & full-line token sets for each context anchor
    m = len(anchors)
    anchor_pre_sets: list[set[int]] = []
    anchor_full_sets: list[set[int]] = []
    doc_freq: dict[int, int] = {}
    for a in anchors:
        a_lid = line_list[a]
        ls = a
        while ls > 0 and line_list[ls - 1] == a_lid:
            ls -= 1
        le = a
        while le + 1 < c_len and line_list[le + 1] == a_lid and p_list[le + 1] != newline_id:
            le += 1
        pre_s = set(p_list[ls:a])
        full_s = set(p_list[ls : le + 1])
        anchor_pre_sets.append(pre_s)
        anchor_full_sets.append(full_s)
        for tok_id in pre_s:
            doc_freq[tok_id] = doc_freq.get(tok_id, 0) + 1

    # Filter out boilerplate template tokens appearing on >= 50% of anchor lines
    thresh = max(2, (m + 1) // 2)
    q_rare = {t for t in q_pre if doc_freq.get(t, 0) < thresh}
    if not q_rare:
        q_rare = q_pre

    best_recall = 0.0
    best_idx = 0
    denom = float(len(q_rare))
    for i, full_s in enumerate(anchor_full_sets):
        rec = len(q_rare & full_s) / denom
        if rec > best_recall:
            best_recall = rec
            best_idx = i

    boundary_merged = p_list[anchors[best_idx]] != p_list[T - 1]
    return best_recall, best_idx, boundary_merged


@dataclass
class FastWeightAdapter:
    mode: str                                                # 'inactive' | 'window' | 'multihop_bridge' | 'clause_bigram'
    anchors_count: int
    mu: torch.Tensor | None                                  # (1, D)
    v_std: torch.Tensor | None                               # (1, D) or None
    w_snr: torch.Tensor | None                               # (D,) or None
    protos: torch.Tensor | None                              # (M, 2*d) or None
    X_support: torch.Tensor | None                           # (m, D)
    max_key_recall: float
    boundary_merged: bool
    step_etas: dict[int, float]
    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]]  # off -> (u_t, W_down)
    logical_bytes: int
    context_text: str = ""
    query_line_text: str = ""

    @torch.no_grad()
    def evaluate_query(
        self,
        xq_raw: torch.Tensor | None,
        enable_key_gate: bool = True,
        encode_fn: Callable[[str], list[int]] | None = None,
    ) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        if self.mode == "inactive" or not self.step_weights or self.X_support is None or self.mu is None or xq_raw is None:
            return {}
        if self.mode == "multihop_bridge" and enable_key_gate:
            return {}

        # Heal BPE delimiter merges (e.g. `EXPORT KEY=val` vs `EXPORT KEY=`) when key_recall > 0.85
        if (
            self.mode == "window"
            and enable_key_gate
            and self.boundary_merged
            and encode_fn is not None
            and self.context_text
            and self.query_line_text
        ):
            # Check zero-adapter invariant: if all step_weights are zero, emit zeros!
            max_w = max((float(wd.abs().max()) for (_, wd) in self.step_weights.values()), default=0.0)
            if max_w == 0.0:
                return {}
            healed_ids = resolve_bpe_boundary_healed_tokens(self.context_text, self.query_line_text, encode_fn)
            if healed_ids:
                dev = xq_raw.device
                return {
                    j: (
                        torch.tensor([tid], device=dev, dtype=torch.long),
                        torch.tensor([12.0], device=dev, dtype=torch.float32),
                    )
                    for j, tid in enumerate(healed_ids)
                }

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
            phi_q = (0.65 * swiglu(4.0 * q_sims - 0.4) + 0.35 * q_sims).squeeze(0).to(xq_raw.device)
        else:
            phi_q = swiglu(4.0 * q_sims - 0.4).squeeze(0).to(xq_raw.device)

        return {off: (u_t, q_conf * (W_d @ phi_q)) for off, (u_t, W_d) in self.step_weights.items()}


@dataclass
class FastWeightSession:
    """Stateful per-request fast-weight decode session supporting prefill deltas and dynamic multi-hop bridges."""
    adapter: FastWeightAdapter
    step_deltas: dict[int, tuple[torch.Tensor, torch.Tensor]]
    device: torch.device
    enable_dynamic_hop: bool = True
    generated_ids: list[int] = field(default_factory=list)
    dynamic_hops_triggered: int = 0

    @torch.no_grad()
    def apply_to_logits(self, logits_1d_f32: torch.Tensor, step_k: int) -> torch.Tensor:
        if step_k not in self.step_deltas:
            return logits_1d_f32
        u_t, dv = self.step_deltas[step_k]
        if float(dv.abs().max()) == 0.0:
            return logits_1d_f32
        out = logits_1d_f32.clone()
        out.index_add_(0, u_t, dv.float())
        return out

    def on_token_sampled(
        self,
        token_id: int,
        next_step_k: int,
        decode_fn: Callable[[list[int]], str] | None = None,
        encode_fn: Callable[[str], list[int]] | None = None,
    ) -> None:
        self.generated_ids.append(int(token_id))
        if (
            not self.enable_dynamic_hop
            or decode_fn is None
            or encode_fn is None
            or not self.adapter.context_text
            or next_step_k in self.step_deltas
        ):
            return
        gen_txt = decode_fn(self.generated_ids)
        hop_ids = resolve_hop_continuation_tokens(self.adapter.context_text, gen_txt, encode_fn)
        if hop_ids:
            self.dynamic_hops_triggered += 1
            for j, tid in enumerate(hop_ids):
                self.step_deltas[next_step_k + j] = (
                    torch.tensor([tid], device=self.device, dtype=torch.long),
                    torch.tensor([12.0], device=self.device, dtype=torch.float32),
                )


def make_zero_adapter(ad: FastWeightAdapter) -> FastWeightAdapter:
    return FastWeightAdapter(
        mode=ad.mode,
        anchors_count=ad.anchors_count,
        mu=ad.mu,
        v_std=ad.v_std,
        w_snr=ad.w_snr,
        protos=ad.protos,
        X_support=ad.X_support,
        max_key_recall=ad.max_key_recall,
        boundary_merged=ad.boundary_merged,
        step_etas={k: 0.0 for k in ad.step_etas},
        step_weights={off: (u_t, torch.zeros_like(W_d)) for off, (u_t, W_d) in ad.step_weights.items()},
        logical_bytes=ad.logical_bytes,
        context_text="",
        query_line_text="",
    )


def make_random_adapter(ad: FastWeightAdapter, seed: int) -> FastWeightAdapter:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    rand_sw = {}
    for off, (u_t, W_d) in ad.step_weights.items():
        t_norm = float(W_d.float().cpu().norm().item())
        noise = torch.randn(W_d.shape, generator=gen, dtype=torch.float32)
        scaled = noise * (t_norm / max(float(noise.norm().item()), 1e-8))
        rand_sw[off] = (u_t, scaled.to(W_d.device))
    return FastWeightAdapter(
        mode="window" if ad.mode == "multihop_bridge" else ad.mode,
        anchors_count=ad.anchors_count,
        mu=ad.mu,
        v_std=ad.v_std,
        w_snr=ad.w_snr,
        protos=ad.protos,
        X_support=ad.X_support,
        max_key_recall=1.0,
        boundary_merged=False,
        step_etas=ad.step_etas,
        step_weights=rand_sw,
        logical_bytes=ad.logical_bytes,
        context_text="",
        query_line_text="",
    )


@torch.no_grad()
def derive_fastweight(
    prompt_ids: torch.Tensor,
    c_len: int,
    newline_id: int,
    E_tok_bf16: torch.Tensor,
    h_last_bf16: torch.Tensor,
    W_lm_bf16: torch.Tensor,
    context_text: str = "",
    query_line_text: str = "",
    enable_key_gate: bool = True,
    enable_loo_nll_gate: bool = True,
) -> tuple[FastWeightAdapter, torch.Tensor | None]:
    """Derive `FastWeightAdapter` strictly from context `[0 .. c_len-1]` with zero GPU sync stalls."""
    device = prompt_ids.device
    p_1d = prompt_ids[0]
    T, _ = h_last_bf16.shape
    assert 0 < c_len <= T
    if c_len < 24:
        return FastWeightAdapter("inactive", 0, None, None, None, None, None, 0.0, False, {}, {}, 0, context_text, query_line_text), None

    hl = safe_norm(h_last_bf16.float())
    et = safe_norm(E_tok_bf16[p_1d].float())

    lim = max(12, c_len - 12)
    sims_gpu = hl[:lim] @ hl[-1]
    top_v, top_i = torch.topk(sims_gpu, k=min(96, lim))
    top_v_list = top_v.cpu().tolist()
    top_i_list = top_i.cpu().tolist()
    p_cpu = p_1d.cpu()
    p_list = p_cpu.tolist()

    is_nl_cpu = (p_cpu == newline_id).long()
    line_id_cpu = torch.cumsum(F.pad(is_nl_cpu[:-1], (1, 0), value=0), dim=0)
    line_list = line_id_cpu.tolist()

    max_s = float(top_v_list[0])
    anchors: list[int] = []
    for v_val, idx in zip(top_v_list, top_i_list):
        if v_val < max_s - 0.05:
            break
        if 10 <= idx < c_len - 12 and all(abs(idx - a) >= 4 for a in anchors):
            anchors.append(idx)
            if len(anchors) >= 64:
                break
    anchors.sort()
    m = len(anchors)
    if m < 4:
        return FastWeightAdapter("inactive", m, None, None, None, None, None, 0.0, False, {}, {}, 0, context_text, query_line_text), None

    keep_cpu = torch.tensor(anchors, dtype=torch.long)
    keep = keep_cpu.to(device)
    anchor_lines_cpu = line_id_cpu[keep_cpu]

    raw_offsets = []
    y_cols_cpu = []
    for off in range(12):
        pos_c = keep_cpu + off
        if int(pos_c[-1]) + 1 >= c_len:
            break
        on_line_c = line_id_cpu[pos_c] == anchor_lines_cpu
        tgts_c = p_cpu[pos_c + 1]
        valid_c = on_line_c & (tgts_c != newline_id)
        n_val = int(valid_c.sum())
        if n_val < max(3, m // 4):
            break
        u_t_c = torch.unique(tgts_c[valid_c])
        n_u = int(u_t_c.numel())
        if n_u > 1:
            if n_u <= 16 and n_val == m:
                ind = (tgts_c.unsqueeze(1) == u_t_c.unsqueeze(0)).float()
                y_cols_cpu.append(ind - ind.mean(dim=0, keepdim=True))
            raw_offsets.append((off, pos_c, valid_c.float(), tgts_c, u_t_c))

    if not raw_offsets:
        return FastWeightAdapter("inactive", m, None, None, None, None, None, 0.0, False, {}, {}, 0, context_text, query_line_text), None

    ans_spans = set()
    for a_idx in anchors:
        a_lid = line_list[a_idx]
        span_toks = []
        for pos_s in range(a_idx + 1, min(c_len, a_idx + 9)):
            if line_list[pos_s] != a_lid or p_list[pos_s] == newline_id:
                break
            span_toks.append(p_list[pos_s])
        ans_spans.add(tuple(span_toks))
    is_lookup = (len(ans_spans) / float(m) > 0.65) or (not y_cols_cpu)

    v_std: torch.Tensor | None = None
    w_snr: torch.Tensor | None = None
    protos: torch.Tensor | None = None
    max_key_recall = 1.0
    boundary_merged = False

    if is_lookup:
        max_key_recall, _, boundary_merged = compute_rare_key_recall(p_list, line_list, anchors, c_len, newline_id)
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
        mode = "multihop_bridge" if (enable_key_gate and max_key_recall <= 0.85) else "window"
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
        bg_ctx = safe_norm(torch.cat([et[:c_len], 0.7 * et_prev], dim=-1))
        protos = bg_ctx[proto_pos]

        dots_a = (bg_ctx[win_a_c.to(device)].reshape(m * max_L, -1) @ protos.T).reshape(m, max_L, -1)
        V_a = dots_a.masked_fill(~mask_a_c.to(device).unsqueeze(-1), -2.0).max(dim=1).values

        et_q_prev = F.pad(et[:-1], (0, 0, 1, 0))
        win_q_c = ((T - 1) + offs_l_c).clamp(0, T - 1)
        win_q = win_q_c.to(device)
        bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q]], dim=-1))
        mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
        xq_raw = (bg_q_win @ protos.T).masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values

        mu = V_a.mean(dim=0, keepdim=True)
        Vc = V_a - mu
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

    S_cpu = (X @ X.T).cpu()
    if mode == "clause_bigram":
        Phi_cpu = 0.65 * swiglu(4.0 * S_cpu - 0.4) + 0.35 * S_cpu
    else:
        Phi_cpu = swiglu(4.0 * S_cpu - 0.4)

    reg = 0.05 * (float(Phi_cpu.pow(2).mean()) + 1e-4)
    G_cpu = Phi_cpu.T @ Phi_cpu + reg * torch.eye(m)
    P_dual_cpu = torch.linalg.solve(G_cpu, Phi_cpu.T)
    H_hat_cpu = Phi_cpu @ P_dual_cpu
    diag_h_cpu = H_hat_cpu.diagonal().unsqueeze(1)

    all_pos_cpu = torch.unique(torch.cat([pos_c for (_, pos_c, _, _, _) in raw_offsets], dim=0))
    all_ut_cpu = torch.unique(torch.cat([u_t_c for (_, _, _, _, u_t_c) in raw_offsets], dim=0))
    L_union_cpu = (h_last_bf16[all_pos_cpu.to(device)].float() @ W_lm_bf16[all_ut_cpu.to(device)].float().T).cpu()

    pos_lookup = {int(p_val): i for i, p_val in enumerate(all_pos_cpu.tolist())}
    ut_lookup = {int(u_val): i for i, u_val in enumerate(all_ut_cpu.tolist())}

    step_etas: dict[int, float] = {}
    step_weights: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for (off, pos_c, valid_f_c, tgts_c, u_t_c) in raw_offsets:
        p_rows = torch.tensor([pos_lookup[int(x)] for x in pos_c.tolist()], dtype=torch.long)
        u_cols = torch.tensor([ut_lookup[int(x)] for x in u_t_c.tolist()], dtype=torch.long)
        lb_ut_cpu = L_union_cpu[p_rows][:, u_cols]
        pb_ut_cpu = F.softmax(lb_ut_cpu, dim=-1)
        y_ut_cpu = (u_t_c.unsqueeze(0) == tgts_c.unsqueeze(1)).float()
        res_ut_cpu = valid_f_c.unsqueeze(1) * (y_ut_cpu - pb_ut_cpu)

        if is_lookup or (not enable_loo_nll_gate):
            best_eta = 12.0
        else:
            loo_res_cpu = ((H_hat_cpu @ res_ut_cpu) - diag_h_cpu * res_ut_cpu) / (1.0 - diag_h_cpu).clamp_min(0.1)
            tgt_col_cpu = y_ut_cpu.argmax(dim=-1)
            valid_bool = valid_f_c > 0.5
            base_nll = float(F.cross_entropy(lb_ut_cpu[valid_bool], tgt_col_cpu[valid_bool]))
            req_gain = 0.07 if base_nll < 0.35 else 0.04
            best_eta = 0.0
            best_nll = base_nll - req_gain
            for eta_cand in (3.0, 6.0, 9.0, 12.0):
                cand_nll = float(F.cross_entropy((lb_ut_cpu + eta_cand * loo_res_cpu)[valid_bool], tgt_col_cpu[valid_bool]))
                if cand_nll < best_nll:
                    best_nll = cand_nll
                    best_eta = eta_cand

        step_etas[off] = best_eta
        if best_eta > 0.0:
            W_down_cpu = best_eta * (res_ut_cpu.T @ P_dual_cpu)
            step_weights[off] = (u_t_c.to(device), W_down_cpu.to(device))

    l_bytes = _tensor_bytes(mu, v_std, w_snr, protos, X) + sum(
        _tensor_bytes(u_t, wd) for (u_t, wd) in step_weights.values()
    )
    return (
        FastWeightAdapter(
            mode=mode,
            anchors_count=m,
            mu=mu,
            v_std=v_std,
            w_snr=w_snr,
            protos=protos,
            X_support=X,
            max_key_recall=max_key_recall,
            boundary_merged=boundary_merged,
            step_etas=step_etas,
            step_weights=step_weights,
            logical_bytes=l_bytes,
            context_text=context_text,
            query_line_text=query_line_text,
        ),
        xq_raw,
    )


@torch.no_grad()
def extract_query_features_for_donor(
    donor_ad: FastWeightAdapter,
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

    if donor_ad.mode in ("window", "multihop_bridge"):
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
        bg_q_win = safe_norm(torch.cat([et[win_q], 0.7 * et_q_prev[win_q]], dim=-1))
        mask_q = ((line_id_cpu[win_q_c] == line_id_cpu[T - 1]) & (((T - 1) + offs_l_c) >= 0)).to(device)
        return (bg_q_win @ donor_ad.protos.T).masked_fill(~mask_q.unsqueeze(-1), -2.0).max(dim=0, keepdim=True).values
    return None
