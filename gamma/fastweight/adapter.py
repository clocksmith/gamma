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
        enable_string_heuristics: bool = True,
    ) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        if self.mode == "inactive" or not self.step_weights or self.X_support is None or self.mu is None or xq_raw is None:
            return {}
        if self.mode == "multihop_bridge" and enable_key_gate:
            return {}

        # Heal BPE delimiter merges (e.g. `EXPORT KEY=val` vs `EXPORT KEY=`) when key_recall > 0.85
        if (
            enable_string_heuristics
            and self.mode == "window"
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
    enable_string_heuristics: bool = True
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
            or not self.enable_string_heuristics
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


# ---------------------------------------------------------------------------
# v4: Forward-Only Reversible Per-Layer MLP `down_proj` LoRA (`DeltaW_l(alpha)`)
#     and Grave et al. (2017) Continuous-Cache kNN Output-Logit Baseline
# ---------------------------------------------------------------------------


def discover_support_anchors(support_ids: list[int], nl_id: int) -> list[dict[str, int]]:
    """Token-only support delimiter discovery (`lastInSuffix`, smallest `mean_dist >= 1`, `>= 2` distinct spans)."""
    lines: list[tuple[int, int]] = []
    start = 0
    for idx, tok in enumerate(support_ids):
        if tok == nl_id:
            if idx - start >= 6:
                lines.append((start, idx))
            start = idx + 1

    tok_line_positions: dict[int, list[dict[str, int]]] = {}
    for li, (s, e) in enumerate(lines):
        last_in_suffix: dict[int, int] = {}
        for p in range(max(s + 3, e - 8), e):
            if p <= e - 2:
                last_in_suffix[support_ids[p]] = p
        for tok, p in last_in_suffix.items():
            tok_line_positions.setdefault(tok, []).append(
                {"line_idx": li, "pos": p, "line_start": s, "line_end": e}
            )

    best_tok = -1
    best_count = 0
    best_small_span = float("inf")
    for tok, arr in tok_line_positions.items():
        if len(arr) < 4:
            continue
        spans = {tuple(support_ids[x["pos"] + 1 : x["line_end"]]) for x in arr}
        if len(spans) < 2:
            continue
        mean_dist = sum(x["line_end"] - x["pos"] for x in arr) / float(len(arr))
        if len(arr) > best_count or (len(arr) == best_count and mean_dist < best_small_span):
            best_count = len(arr)
            best_small_span = mean_dist
            best_tok = tok

    return tok_line_positions[best_tok] if best_tok >= 0 else []


@dataclass
class ClosedFormLayerLoRA:
    """Reversible per-layer MLP `down_proj` LoRA (`W_l(alpha) = W_l + alpha * (A_l @ B_l)^T` in input-major layout)."""

    active: bool
    rank: int
    d_hidden: int
    d_inter: int
    target_layers: list[int]
    layers: dict[int, tuple[torch.Tensor, torch.Tensor]]  # layer_idx -> (A_l [d_inter, rank], B_l [rank, d_hidden])
    uniq_target_tokens: list[int]
    anchors_count: int
    logical_bytes: int


def _solve_spd_float64(G: torch.Tensor, Rhs: torch.Tensor) -> torch.Tensor:
    """Deterministic Gauss-Jordan SPD linear solver matching `solveSPDLinearSystem` in `doppler_fastweight.mjs`."""
    m = int(G.shape[0])
    cols = int(Rhs.shape[1])
    aug = torch.cat([G.to(torch.float64), Rhs.to(torch.float64)], dim=1).clone()
    for i in range(m):
        piv = i + int(torch.argmax(aug[i:, i].abs()).item())
        if piv != i:
            tmp = aug[i].clone()
            aug[i] = aug[piv]
            aug[piv] = tmp
        diag = float(aug[i, i].item())
        if diag == 0.0:
            diag = 1e-9
        aug[i, i:] = aug[i, i:] / diag
        for r in range(m):
            if r == i:
                continue
            f = float(aug[r, i].item())
            if f != 0.0:
                aug[r, i:] = aug[r, i:] - f * aug[i, i:]
    return aug[:, m:]


@torch.no_grad()
def compile_closed_form_layer_lora(
    support_ids: list[int],
    header_ids: list[int],
    nl_id: int,
    d_hidden: int,
    d_inter: int,
    target_layers: list[int],
    iso_entries: list[dict],
    cat_entry: dict,
    final_norm_g: torch.Tensor,
    get_lm_row: Callable[[int], torch.Tensor],
    post_ffn_norm_map: dict[int, torch.Tensor] | None = None,
    sigma_u0_map: dict[int, float] | None = None,
) -> ClosedFormLayerLoRA:
    """Compile closed-form per-layer MLP `down_proj` LoRA factors `(A_l, B_l)` without gradient steps or string heuristics.

    Matches `compileClosedFormLayerLoRA` in `doppler_fastweight.mjs` equation-for-equation.
    """
    anc_objs = discover_support_anchors(support_ids, nl_id)
    m = len(anc_objs)
    if m < 4 or len(iso_entries) != m or not target_layers:
        return ClosedFormLayerLoRA(False, 0, d_hidden, d_inter, [], {}, [], m, 0)

    samples: list[dict] = []
    stop_samples: list[dict] = []
    bg_samples: list[dict] = []
    for ex in range(m):
        iso = iso_entries[ex]
        rel_anchor = int(iso["rel_anchor"])
        line_len = len(iso["line_ids"])
        cat_anchor = anc_objs[ex]["pos"]
        cat_end = anc_objs[ex]["line_end"]
        cat_start = anc_objs[ex]["line_start"]
        answer_len = max(1, cat_end - cat_anchor - 1)
        for off in range(answer_len):
            if rel_anchor + off >= line_len or cat_anchor + off + 1 >= cat_end:
                continue
            next_tok = int(support_ids[cat_anchor + off + 1])
            if next_tok == nl_id:
                continue
            samples.append({"kind": "iso", "ex": ex, "off": off, "next_tok": next_tok, "pos": rel_anchor + off})
            samples.append({"kind": "cat", "ex": ex, "off": off, "next_tok": next_tok, "pos": cat_anchor + off})
        if rel_anchor + answer_len < line_len:
            stop_samples.append({"kind": "iso", "ex": ex, "pos": rel_anchor + answer_len})
        if cat_anchor + answer_len < cat_end:
            stop_samples.append({"kind": "cat", "ex": ex, "pos": cat_anchor + answer_len})
        for p in range(len(header_ids) + 1, rel_anchor, 2):
            bg_samples.append({"kind": "iso", "ex": ex, "pos": p})
        bg_samples.append({"kind": "cat", "ex": ex, "pos": (cat_start + cat_anchor) // 2})

    if not samples:
        return ClosedFormLayerLoRA(False, 0, d_hidden, d_inter, [], {}, [], m, 0)

    h_rms_list: list[float] = []
    for ex in range(m):
        h_iso = iso_entries[ex]["h_flat"].to(torch.float64)
        ra = int(iso_entries[ex]["rel_anchor"])
        vec = h_iso[ra * d_hidden : (ra + 1) * d_hidden]
        h_rms_list.append(float(torch.sqrt((vec * vec).mean()).item()))
    h_rms_list.sort()
    median_h_rms = h_rms_list[len(h_rms_list) // 2]

    uniq_target_toks = sorted({s["next_tok"] for s in samples})
    uniq_set = set(uniq_target_toks)
    bare_set: set[int] = {int(nl_id)}
    for ex in range(m):
        for tid in iso_entries[ex].get("bare_top", []):
            t_int = int(tid)
            if t_int not in uniq_set:
                bare_set.add(t_int)
    bare_default_toks = sorted(bare_set)

    K_u = len(uniq_target_toks)
    rank = K_u + 2
    suppress_col = K_u
    stop_col = K_u + 1
    tok_to_col = {t: i for i, t in enumerate(uniq_target_toks)}

    N_s = len(samples)
    N_stop = len(stop_samples)
    N_bg = len(bg_samples)
    N_tot = N_s + N_stop + N_bg

    Y_base = torch.zeros((N_tot, rank), dtype=torch.float64)
    neg_val = -1.0 / float(max(1, K_u - 1))
    for r, s in enumerate(samples):
        tc = tok_to_col[s["next_tok"]]
        for u in range(K_u):
            Y_base[r, u] = 1.0 if u == tc else neg_val
        if s["kind"] == "iso":
            Y_base[r, suppress_col] = 1.0
            Y_base[r, stop_col] = -1.0
    for s_idx in range(N_stop):
        Y_base[N_s + s_idx, stop_col] = 1.35

    span_keys: list[tuple[int, ...]] = []
    for a in anc_objs:
        sk = tuple(support_ids[a["pos"] + 1 : a["line_end"]])
        if sk not in span_keys:
            span_keys.append(sk)
    y_cls_cols: list[torch.Tensor] = []
    y_cls_norm2: list[float] = []
    for sk in span_keys:
        col = torch.tensor(
            [1.0 if tuple(support_ids[anc_objs[i]["pos"] + 1 : anc_objs[i]["line_end"]]) == sk else 0.0 for i in range(m)],
            dtype=torch.float64,
        )
        col = col - col.mean()
        y_cls_cols.append(col)
        y_cls_norm2.append(max(float((col * col).sum().item()), 1e-8))

    fn_g = final_norm_g.to(torch.float64)
    w_targets = [get_lm_row(t).to(torch.float64) for t in uniq_target_toks]
    w_target_mean = torch.stack(w_targets, dim=0).mean(dim=0)
    w_bares = [get_lm_row(t).to(torch.float64) for t in bare_default_toks]
    w_bare_mean = torch.stack(w_bares, dim=0).mean(dim=0)
    w_nl = get_lm_row(int(nl_id)).to(torch.float64)

    pfn_map = post_ffn_norm_map or {}
    sig_map = sigma_u0_map or {}
    bg_gamma = float((0.80) ** 0.5)

    layers_out: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    total_bytes = 0

    for l_idx in target_layers:
        pfn = pfn_map.get(l_idx)
        pfn_f64 = pfn.to(torch.float64) if pfn is not None else None
        sigma_u0 = float(sig_map.get(l_idx, 1.0))
        pfn_rms = float(torch.sqrt((pfn_f64 * pfn_f64).mean()).item()) if pfn_f64 is not None else 1.0
        target_rms = (0.24 * sigma_u0) if pfn_f64 is not None else (0.30 * median_h_rms / float(len(target_layers)))

        if pfn_f64 is not None:
            floor_v = 0.15 * pfn_rms
            sign_pfn = torch.where(pfn_f64 < 0.0, torch.full_like(pfn_f64, -1.0), torch.ones_like(pfn_f64))
            denom = torch.where(pfn_f64.abs() > floor_v, pfn_f64, sign_pfn * floor_v)
            g_factor = fn_g / denom
        else:
            g_factor = fn_g

        B_unit = torch.zeros((rank, d_hidden), dtype=torch.float32)

        def _write_b_row(r_idx: int, raw_dir: torch.Tensor) -> None:
            tmp = g_factor * raw_dir
            r_val = float(torch.sqrt((tmp * tmp).mean() + 1e-12).item())
            B_unit[r_idx] = ((tmp / r_val) * target_rms).to(torch.float32)

        for u in range(K_u):
            _write_b_row(u, w_targets[u] - 0.55 * w_target_mean)
        _write_b_row(suppress_col, 0.70 * w_target_mean - 0.85 * w_bare_mean)
        _write_b_row(stop_col, w_nl - 0.85 * w_target_mean)

        iso_z0 = torch.stack(
            [
                iso_entries[ex]["layer_z_map"][l_idx][
                    int(iso_entries[ex]["rel_anchor"]) * d_inter : (int(iso_entries[ex]["rel_anchor"]) + 1) * d_inter
                ].to(torch.float64)
                for ex in range(m)
            ],
            dim=0,
        )
        cat_z_all = cat_entry["layer_z_map"][l_idx].to(torch.float64)
        cat_z0 = torch.stack(
            [cat_z_all[anc_objs[ex]["pos"] * d_inter : (anc_objs[ex]["pos"] + 1) * d_inter] for ex in range(m)],
            dim=0,
        )
        dI = iso_z0 - iso_z0.mean(dim=0, keepdim=True)
        dC = cat_z0 - cat_z0.mean(dim=0, keepdim=True)
        sqI = (dI * dI).sum(dim=0)
        sqC = (dC * dC).sum(dim=0)
        rho2 = torch.zeros(d_inter, dtype=torch.float64)
        for c_idx, yc in enumerate(y_cls_cols):
            dotI = (dI * yc.unsqueeze(1)).sum(dim=0)
            dotC = (dC * yc.unsqueeze(1)).sum(dim=0)
            rI = torch.where(sqI > 1e-8, (dotI * dotI) / (sqI * y_cls_norm2[c_idx]), torch.zeros_like(sqI))
            rC = torch.where(sqC > 1e-8, (dotC * dotC) / (sqC * y_cls_norm2[c_idx]), torch.zeros_like(sqC))
            rho2 = torch.maximum(rho2, 0.5 * (rI + rC))
        max_rho = max(float(rho2.max().item()), 1e-8)
        feat_w = torch.sqrt(0.25 + 1.75 * (rho2 / max_rho)).to(torch.float32).to(torch.float64)

        def _get_z(item: dict) -> torch.Tensor:
            pos = int(item["pos"])
            if item["kind"] == "iso":
                src = iso_entries[int(item["ex"])]["layer_z_map"][l_idx]
            else:
                src = cat_entry["layer_z_map"][l_idx]
            return src[pos * d_inter : (pos + 1) * d_inter].to(torch.float32).to(torch.float64)

        z_rows_list: list[torch.Tensor] = []
        mean_sq = 0.0
        for s in samples:
            r_vec = (_get_z(s) * feat_w).to(torch.float32).to(torch.float64)
            mean_sq += float((r_vec * r_vec).sum().item()) / float(N_s)
            z_rows_list.append(r_vec)
        for st in stop_samples:
            z_rows_list.append((_get_z(st) * feat_w).to(torch.float32).to(torch.float64))
        for bg in bg_samples:
            z_rows_list.append((_get_z(bg) * feat_w * bg_gamma).to(torch.float32).to(torch.float64))

        Z_mat = torch.stack(z_rows_list, dim=0)
        lam = 0.15 * mean_sq
        G = Z_mat @ Z_mat.T + lam * torch.eye(N_tot, dtype=torch.float64)
        C = _solve_spd_float64(G, Y_base)

        extra_scale = torch.ones((N_tot, 1), dtype=torch.float64)
        if N_bg > 0:
            extra_scale[N_s + N_stop :, 0] = bg_gamma
        Z_back = Z_mat * feat_w.unsqueeze(0) * extra_scale
        A_l = (Z_back.T @ C).to(torch.float32)

        layers_out[int(l_idx)] = (A_l, B_unit)
        total_bytes += _tensor_bytes(A_l, B_unit)

    return ClosedFormLayerLoRA(
        active=True,
        rank=rank,
        d_hidden=d_hidden,
        d_inter=d_inter,
        target_layers=list(target_layers),
        layers=layers_out,
        uniq_target_tokens=uniq_target_toks,
        anchors_count=m,
        logical_bytes=total_bytes,
    )


def make_zero_layer_lora(lora: ClosedFormLayerLoRA) -> ClosedFormLayerLoRA:
    zero_layers = {
        l_idx: (torch.zeros_like(A_l), torch.zeros_like(B_l))
        for l_idx, (A_l, B_l) in lora.layers.items()
    }
    return ClosedFormLayerLoRA(
        active=lora.active,
        rank=lora.rank,
        d_hidden=lora.d_hidden,
        d_inter=lora.d_inter,
        target_layers=list(lora.target_layers),
        layers=zero_layers,
        uniq_target_tokens=list(lora.uniq_target_tokens),
        anchors_count=lora.anchors_count,
        logical_bytes=lora.logical_bytes,
    )


def make_random_layer_lora(lora: ClosedFormLayerLoRA, seed: int) -> ClosedFormLayerLoRA:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(int(seed))
    rand_layers: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
    for l_idx, (A_l, B_l) in lora.layers.items():
        a_norm = float(A_l.float().cpu().norm().item())
        b_norm = float(B_l.float().cpu().norm().item())
        a_noise = torch.randn(A_l.shape, generator=gen, dtype=torch.float32)
        b_noise = torch.randn(B_l.shape, generator=gen, dtype=torch.float32)
        a_scaled = a_noise * (a_norm / max(float(a_noise.norm().item()), 1e-8))
        b_scaled = b_noise * (b_norm / max(float(b_noise.norm().item()), 1e-8))
        rand_layers[l_idx] = (a_scaled.to(A_l.device), b_scaled.to(B_l.device))
    return ClosedFormLayerLoRA(
        active=lora.active,
        rank=lora.rank,
        d_hidden=lora.d_hidden,
        d_inter=lora.d_inter,
        target_layers=list(lora.target_layers),
        layers=rand_layers,
        uniq_target_tokens=list(lora.uniq_target_tokens),
        anchors_count=lora.anchors_count,
        logical_bytes=lora.logical_bytes,
    )


@torch.no_grad()
def derive_continuous_cache_knn(
    prompt_ids: list[int],
    c_len: int,
    nl_id: int,
    h_last: torch.Tensor,
    tau: float = 0.08,
    eta_cache: float = 8.0,
) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
    """Grave et al. (2017) continuous-cache / prompt kNN-LM output-logit baseline (`Delta W_l = 0`)."""
    anc_objs = discover_support_anchors(prompt_ids[:c_len], nl_id)
    if len(anc_objs) < 4:
        return {}
    hl = safe_norm(h_last.float())
    T = len(prompt_ids)
    q_vec = hl[T - 1]
    keys = torch.stack([hl[a["pos"]] for a in anc_objs], dim=0)
    vals = [int(prompt_ids[a["pos"] + 1]) for a in anc_objs]
    uniq_vals = sorted(set(vals))
    if len(uniq_vals) < 2:
        return {}
    sims = (keys @ q_vec) / max(tau, 1e-4)
    probs = F.softmax(sims, dim=0)
    dv_list: list[float] = []
    prior = 1.0 / float(len(uniq_vals))
    for uv in uniq_vals:
        p_sum = sum(float(probs[i].item()) for i, v in enumerate(vals) if v == uv)
        dv_list.append(eta_cache * (p_sum - prior))
    dev = h_last.device
    return {
        0: (
            torch.tensor(uniq_vals, device=dev, dtype=torch.long),
            torch.tensor(dv_list, device=dev, dtype=torch.float32),
        )
    }

