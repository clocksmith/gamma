"""Paired-switch PyTorch transformers engine, tied-row splitting, cache reuse, and forced-call checks.

Implements Sections 2 and 3 of the BITS paired-switch experiment:
- Independent single-row adaptation of output row W_out[<H0>] and input
  embedding E_in[<H0>] even when `tie_word_embeddings=True`, without mutating
  any other vocabulary row or any backbone parameter.
- Parameter-invariance audit (bit-exact checksums + max_abs_diff == 0.0).
- Equal-budget adaptation across Frozen, Score-only, and Score-and-input arms.
- Forward-only KV-cache reuse with fresh-row rescoring (never stale logits)
  and full-rebuild numerical parity verification.
- Forced-call isolation check (exact shared output row, toggle only E_in[<H0>],
  strict zero pre-call difference gate, post-call difference measurement).
"""

from __future__ import annotations

import copy
import hashlib
import math
import resource
import time
from dataclasses import dataclass
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import DynamicCache, LlamaConfig, LlamaForCausalLM

from helpers import HELPER_SPECS
from switch_point import assert_helper_token_absent


def _tensor_sha256(t: torch.Tensor) -> str:
    arr = t.detach().cpu().contiguous()
    # View raw bytes safely across dtypes (including bfloat16).
    raw = arr.view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(raw).hexdigest()


def extract_kv_pairs(past_key_values: Any) -> list[tuple[torch.Tensor, torch.Tensor]]:
    """Extract (key, value) tensor pairs across transformers 4.x and 5.x cache types."""
    if past_key_values is None:
        return []
    if hasattr(past_key_values, "layers") and past_key_values.layers:
        return [(layer.keys, layer.values) for layer in past_key_values.layers]
    if hasattr(past_key_values, "key_cache") and hasattr(past_key_values, "value_cache"):
        return list(zip(past_key_values.key_cache, past_key_values.value_cache))
    if isinstance(past_key_values, (tuple, list)):
        return [(kv[0], kv[1]) for kv in past_key_values]
    raise TypeError(f"Unsupported past_key_values type: {type(past_key_values)}")


def clone_kv_cache(past_key_values: Any) -> DynamicCache:
    """Deep-clone a KV cache into an independent DynamicCache."""
    pairs = extract_kv_pairs(past_key_values)
    cloned = DynamicCache()
    for layer_idx, (k, v) in enumerate(pairs):
        cloned.update(k.detach().clone(), v.detach().clone(), layer_idx)
    return cloned


def get_peak_rss_bytes() -> int:
    """Return process peak RSS in bytes (macOS reports bytes, Linux KiB)."""
    val = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if torch.backends.mps.is_available():
        return val
    # Heuristic fallback: on Linux ru_maxrss is KiB (< 10^8 for typical procs).
    return val * 1024 if val < 10**8 else val


class ByteLevelTestTokenizer:
    """Deterministic offline byte-level tokenizer with a dedicated reserved `<H0>` ID.

    Used strictly for offline mechanical/numerical verification of Sections 1-3
    when no pretrained HF tokenizer is loaded. Never used for trained-model claims.
    """

    def __init__(self, helper_symbol: str = "<H0>", helper_token_id: int = 259) -> None:
        self.helper_symbol = helper_symbol
        self.pad_token_id = 256
        self.bos_token_id = 257
        self.eos_token_id = 258
        self.helper_token_id = helper_token_id
        self.vocab_size = max(264, helper_token_id + 1)

    def encode(self, text: str) -> list[int]:
        ids: list[int] = []
        parts = text.split(self.helper_symbol)
        for idx, part in enumerate(parts):
            ids.extend(part.encode("utf-8"))
            if idx + 1 < len(parts):
                ids.append(self.helper_token_id)
        return ids

    def decode(self, ids: list[int]) -> str:
        out: list[str] = []
        buf = bytearray()
        for tid in ids:
            if tid == self.helper_token_id:
                if buf:
                    out.append(buf.decode("utf-8", errors="replace"))
                    buf.clear()
                out.append(self.helper_symbol)
            elif 0 <= tid < 256:
                buf.append(tid)
        if buf:
            out.append(buf.decode("utf-8", errors="replace"))
        return "".join(out)


def build_synthetic_transformer(
    *,
    vocab_size: int = 264,
    hidden_size: int = 64,
    num_hidden_layers: int = 2,
    num_attention_heads: int = 4,
    tie_word_embeddings: bool = True,
    seed: int = 1337,
    device: str = "cpu",
    dtype: torch.dtype = torch.float32,
) -> LlamaForCausalLM:
    """Build a real PyTorch transformers LlamaForCausalLM for mechanical verification."""
    torch.manual_seed(seed)
    cfg = LlamaConfig(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        intermediate_size=hidden_size * 2,
        num_hidden_layers=num_hidden_layers,
        num_attention_heads=num_attention_heads,
        num_key_value_heads=num_attention_heads,
        max_position_embeddings=2048,
        tie_word_embeddings=tie_word_embeddings,
        rms_norm_eps=1e-5,
    )
    model = LlamaForCausalLM(cfg).to(device=device, dtype=dtype).eval()
    return model


@dataclass
class PrefillState:
    prefix_token_ids: list[int]
    past_key_values: DynamicCache
    last_hidden_state: torch.Tensor
    stale_logits: torch.Tensor


class PairedSwitchAdapter:
    """Non-invasive single-row overlay for `<H0>` on any PyTorch causal LM.

    Works identically whether `model.config.tie_word_embeddings` is True or False:
    - Backbone weights, embed_tokens.weight, and lm_head.weight are frozen and
      NEVER mutated in place.
    - `delta_in` shifts ONLY `embed_tokens(input_ids)` at positions where `input_ids == h0`.
    - `delta_out` shifts ONLY `lm_head(hidden_states)[..., h0]` via `hidden_states @ delta_out`.
    """

    def __init__(self, model: nn.Module, helper_token_id: int) -> None:
        self.model = model
        self.helper_token_id = int(helper_token_id)
        self.embed = model.get_input_embeddings()
        self.lm_head = model.get_output_embeddings()
        self.hidden_size = int(self.embed.weight.shape[1])
        self.vocab_size = int(self.embed.weight.shape[0])
        self.device = self.embed.weight.device
        self.dtype = self.embed.weight.dtype
        self.tied_embeddings = bool(
            self.embed.weight.data_ptr() == self.lm_head.weight.data_ptr()
        )

        # Freeze every original model parameter and snapshot exact checksums.
        for p in self.model.parameters():
            p.requires_grad_(False)
        self._baseline_checksums = {
            name: _tensor_sha256(param) for name, param in self.model.named_parameters()
        }
        self._orig_embed_weight = self.embed.weight.detach().clone()
        self._orig_lm_head_weight = self.lm_head.weight.detach().clone()

        # Trainable row deltas (default zero = Frozen alias).
        self.delta_out = nn.Parameter(
            torch.zeros(self.hidden_size, device=self.device, dtype=torch.float32),
            requires_grad=False,
        )
        self.delta_in = nn.Parameter(
            torch.zeros(self.hidden_size, device=self.device, dtype=torch.float32),
            requires_grad=False,
        )
        self._captured_last_hidden: torch.Tensor | None = None
        self._capture_hidden_enabled = False

        self._hooks = [
            self.embed.register_forward_hook(self._embed_hook),
            self.lm_head.register_forward_hook(self._lm_head_hook),
        ]

    def close(self) -> None:
        for h in self._hooks:
            h.remove()
        self._hooks.clear()

    def _embed_hook(self, module: nn.Module, args: tuple[Any, ...], output: torch.Tensor) -> torch.Tensor:
        input_ids = args[0]
        if input_ids is None:
            return output
        mask = input_ids == self.helper_token_id
        if not bool(mask.any()):
            return output
        delta = self.delta_in.to(device=output.device, dtype=output.dtype)
        return output + mask.unsqueeze(-1).to(output.dtype) * delta

    def _lm_head_hook(self, module: nn.Module, args: tuple[Any, ...], output: torch.Tensor) -> torch.Tensor:
        hidden = args[0]
        if self._capture_hidden_enabled:
            self._captured_last_hidden = hidden[:, -1:, :].detach().clone()
        if not self.delta_out.requires_grad and float(self.delta_out.detach().abs().max().item()) == 0.0:
            return output
        delta = self.delta_out.to(device=output.device, dtype=hidden.dtype)
        shift = torch.matmul(hidden, delta).to(output.dtype).unsqueeze(-1)
        h0 = self.helper_token_id
        return torch.cat(
            [output[..., :h0], output[..., h0 : h0 + 1] + shift, output[..., h0 + 1 :]],
            dim=-1,
        )

    def set_deltas(
        self,
        delta_out: torch.Tensor | None = None,
        delta_in: torch.Tensor | None = None,
    ) -> None:
        with torch.no_grad():
            if delta_out is None:
                self.delta_out.zero_()
            else:
                self.delta_out.copy_(delta_out.detach().to(device=self.device, dtype=torch.float32))
            if delta_in is None:
                self.delta_in.zero_()
            else:
                self.delta_in.copy_(delta_in.detach().to(device=self.device, dtype=torch.float32))
        self.delta_out.requires_grad_(False)
        self.delta_in.requires_grad_(False)

    def effective_input_row(self, token_id: int) -> torch.Tensor:
        base = self.embed.weight[token_id].detach().to(torch.float32)
        if token_id == self.helper_token_id:
            return base + self.delta_in.detach().to(base.device, dtype=torch.float32)
        return base

    def effective_output_row(self, token_id: int) -> torch.Tensor:
        base = self.lm_head.weight[token_id].detach().to(torch.float32)
        if token_id == self.helper_token_id:
            return base + self.delta_out.detach().to(base.device, dtype=torch.float32)
        return base

    def verify_parameter_invariance(self, arm_name: str) -> dict[str, Any]:
        """Verify backbone and all non-<H0> rows retain bit-exact original values."""
        mismatched_params = []
        for name, param in self.model.named_parameters():
            if _tensor_sha256(param) != self._baseline_checksums[name]:
                mismatched_params.append(name)

        h0 = self.helper_token_id
        other_mask = torch.ones(self.vocab_size, dtype=torch.bool, device=self.device)
        other_mask[h0] = False

        other_embed_max_diff = float(
            (self.embed.weight[other_mask] - self._orig_embed_weight[other_mask]).abs().max().item()
        )
        other_lm_head_max_diff = float(
            (self.lm_head.weight[other_mask] - self._orig_lm_head_weight[other_mask]).abs().max().item()
        )

        h0_out_diff = float(
            (self.effective_output_row(h0) - self._orig_lm_head_weight[h0].to(torch.float32))
            .abs()
            .max()
            .item()
        )
        h0_in_diff = float(
            (self.effective_input_row(h0) - self._orig_embed_weight[h0].to(torch.float32))
            .abs()
            .max()
            .item()
        )

        invariance_ok = (
            len(mismatched_params) == 0
            and other_embed_max_diff == 0.0
            and other_lm_head_max_diff == 0.0
        )
        if arm_name == "frozen_alias":
            arm_contract_ok = h0_out_diff == 0.0 and h0_in_diff == 0.0
        elif arm_name == "score_only_alias":
            arm_contract_ok = h0_out_diff > 0.0 and h0_in_diff == 0.0
        elif arm_name == "score_and_input_alias":
            arm_contract_ok = h0_out_diff > 0.0 and h0_in_diff > 0.0
        else:
            arm_contract_ok = h0_out_diff == 0.0 and h0_in_diff == 0.0

        return {
            "arm": arm_name,
            "tied_embeddings_detected": self.tied_embeddings,
            "mismatched_backbone_params": mismatched_params,
            "other_embed_rows_max_abs_diff": other_embed_max_diff,
            "other_lm_head_rows_max_abs_diff": other_lm_head_max_diff,
            "h0_output_row_max_abs_diff": h0_out_diff,
            "h0_input_row_max_abs_diff": h0_in_diff,
            "backbone_and_other_rows_exact": invariance_ok,
            "arm_row_contract_ok": arm_contract_ok,
        }

    @torch.no_grad()
    def prefill_prefix(self, prefix_token_ids: list[int]) -> PrefillState:
        """Prefill saved prefix once and capture DynamicCache + final pre-head hidden state."""
        if self.helper_token_id in prefix_token_ids:
            raise AssertionError("Helper token ID present in prefix passed to prefill_prefix")
        input_ids = torch.tensor([prefix_token_ids], dtype=torch.long, device=self.device)
        positions = torch.arange(len(prefix_token_ids), dtype=torch.long, device=self.device).unsqueeze(0)
        self._capture_hidden_enabled = True
        self._captured_last_hidden = None
        try:
            out = self.model(
                input_ids=input_ids,
                position_ids=positions,
                use_cache=True,
            )
        finally:
            self._capture_hidden_enabled = False
        assert self._captured_last_hidden is not None
        return PrefillState(
            prefix_token_ids=list(prefix_token_ids),
            past_key_values=clone_kv_cache(out.past_key_values),
            last_hidden_state=self._captured_last_hidden.clone(),
            stale_logits=out.logits[:, -1, :].detach().clone(),
        )

    @torch.no_grad()
    def score_switch_boundary(self, prefill: PrefillState) -> torch.Tensor:
        """Score next decision at switch boundary with CURRENT output row (never stale logits)."""
        return self.lm_head(prefill.last_hidden_state)[:, -1, :].detach().clone()

    @torch.no_grad()
    def forward_from_cache(
        self,
        past_key_values: DynamicCache,
        start_pos: int,
        new_token_ids: list[int],
    ) -> tuple[torch.Tensor, DynamicCache]:
        """Advance cached continuation forward-only with explicit contiguous position IDs."""
        cache = clone_kv_cache(past_key_values)
        if not new_token_ids:
            raise ValueError("new_token_ids must be non-empty")
        logits_steps = []
        pos = start_pos
        for tid in new_token_ids:
            inp = torch.tensor([[tid]], dtype=torch.long, device=self.device)
            pos_ids = torch.tensor([[pos]], dtype=torch.long, device=self.device)
            out = self.model(
                input_ids=inp,
                position_ids=pos_ids,
                past_key_values=cache,
                use_cache=True,
            )
            cache = out.past_key_values
            logits_steps.append(out.logits[:, -1, :].detach().clone())
            pos += 1
        return torch.stack(logits_steps, dim=1), cache


def build_switch_adaptation_sequences(
    snapshot: dict[str, Any],
    tokenizer_encode: Any,
) -> list[dict[str, Any]]:
    """Construct adaptation sequences strictly from information visible at the switch point.

    Zero hidden test cases and zero ground-truth solutions enter here: only the
    switch-time helper exposure, operand convention, boundary behavior table,
    and syntax template visible to all arms.
    """
    helper_name = snapshot["helper_name"]
    spec = HELPER_SPECS[helper_name]
    sym = snapshot["reserved_token"]["helper_token_symbol"]
    exposure = snapshot["switch_exposure"]["alias_arms"]

    # Two switch-visible training cues:
    # (1) Selection cue: exposure + invocation lead-in -> <H0> + exact operand convention.
    # (2) Boundary consumption cue: exposure + boundary call -> expected return usage.
    call_line = spec.call_template.format(OP=sym)
    lhs, rhs = call_line.split(sym, 1)

    seq_texts = [
        f"{exposure}\nUSE_HELPER:\n{lhs}{sym}{rhs}\nreturn {lhs.strip().rstrip('=').strip()}\n",
    ]
    for case in spec.boundary_cases[:3]:
        seq_texts.append(
            f"{exposure}\nCHECK_{case['label']}:\nres = {sym}({case['args_repr']})\n# -> {case['expected_repr']}\n"
        )

    examples = []
    for idx, txt in enumerate(seq_texts):
        ids = [int(t) for t in tokenizer_encode(txt)]
        examples.append({"index": idx, "token_ids": ids, "length": len(ids)})
    return examples


def adapt_arm_equal_budget(
    adapter: PairedSwitchAdapter,
    *,
    arm_name: str,
    adaptation_examples: list[dict[str, Any]],
    setup_budget_steps: int,
    lr: float = 5e-2,
    weight_decay: float = 0.0,
) -> dict[str, Any]:
    """Run equal-budget adaptation for one arm and log exact actual spend."""
    started = time.perf_counter()
    adapter.set_deltas(None, None)

    if arm_name in ("frozen_alias", "ordinary_named_fn") or setup_budget_steps <= 0:
        inv = adapter.verify_parameter_invariance(arm_name)
        return {
            "arm": arm_name,
            "setup_budget_steps": setup_budget_steps,
            "actual_steps": 0,
            "forward_passes": 0,
            "backward_passes": 0,
            "tokens_processed": 0,
            "wall_seconds": time.perf_counter() - started,
            "peak_rss_bytes": get_peak_rss_bytes(),
            "initial_loss": None,
            "final_loss": None,
            "delta_out": adapter.delta_out.detach().clone(),
            "delta_in": adapter.delta_in.detach().clone(),
            "delta_out_l2": 0.0,
            "delta_in_l2": 0.0,
            "invariance": inv,
        }

    if arm_name == "score_only_alias":
        adapter.delta_out.requires_grad_(True)
        adapter.delta_in.requires_grad_(False)
        params = [adapter.delta_out]
    elif arm_name == "score_and_input_alias":
        adapter.delta_out.requires_grad_(True)
        adapter.delta_in.requires_grad_(True)
        params = [adapter.delta_out, adapter.delta_in]
    else:
        raise ValueError(f"Unknown arm_name: {arm_name}")

    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
    h0 = adapter.helper_token_id
    forward_passes = 0
    backward_passes = 0
    tokens_processed = 0
    loss_trace: list[float] = []

    for step in range(setup_budget_steps):
        optimizer.zero_grad(set_to_none=True)
        step_loss = torch.tensor(0.0, device=adapter.device, dtype=torch.float32)
        ex_count = 0
        for ex in adaptation_examples:
            ids = ex["token_ids"]
            if len(ids) < 2:
                continue
            inp = torch.tensor([ids[:-1]], dtype=torch.long, device=adapter.device)
            tgt = torch.tensor([ids[1:]], dtype=torch.long, device=adapter.device)
            out = adapter.model(input_ids=inp, use_cache=False)
            logits = out.logits.to(torch.float32)
            forward_passes += 1
            tokens_processed += inp.shape[1]

            # Loss combines:
            # - selection loss on positions predicting <H0> (supervises delta_out),
            # - post-call continuation loss on positions strictly after <H0> (supervises delta_in + delta_out).
            per_tok = F.cross_entropy(logits.view(-1, logits.shape[-1]), tgt.view(-1), reduction="none")
            tgt_flat = tgt.view(-1)
            inp_flat = inp.view(-1)

            sel_mask = tgt_flat == h0
            # Positions at or after first occurrence of h0 in inp_flat.
            h0_positions = torch.nonzero(inp_flat == h0, as_tuple=False)
            post_mask = torch.zeros_like(sel_mask)
            if h0_positions.numel() > 0:
                first_h0 = int(h0_positions[0].item())
                post_mask[first_h0:] = True

            # Both arms see the exact same sequences and spend the exact same step/forward/backward budget.
            # Score-only spends 100% of its gradient updates on delta_out (selection objective);
            # score-and-input optimizes both delta_out and delta_in jointly.
            if arm_name == "score_only_alias":
                active_mask = sel_mask if bool(sel_mask.any()) else torch.ones_like(sel_mask)
                ex_loss = per_tok[active_mask].mean()
            else:
                loss_terms = []
                if bool(sel_mask.any()):
                    loss_terms.append(per_tok[sel_mask].mean())
                if bool(post_mask.any()):
                    loss_terms.append(per_tok[post_mask].mean())
                ex_loss = sum(loss_terms) / max(1, len(loss_terms))

            step_loss = step_loss + ex_loss
            ex_count += 1

        step_loss = step_loss / max(1, ex_count)
        step_loss.backward()
        backward_passes += 1
        torch.nn.utils.clip_grad_norm_(params, max_norm=1.0)
        optimizer.step()
        loss_trace.append(float(step_loss.detach().item()))

    adapter.delta_out.requires_grad_(False)
    adapter.delta_in.requires_grad_(False)

    inv = adapter.verify_parameter_invariance(arm_name)
    return {
        "arm": arm_name,
        "setup_budget_steps": setup_budget_steps,
        "actual_steps": setup_budget_steps,
        "forward_passes": forward_passes,
        "backward_passes": backward_passes,
        "tokens_processed": tokens_processed,
        "wall_seconds": time.perf_counter() - started,
        "peak_rss_bytes": get_peak_rss_bytes(),
        "initial_loss": loss_trace[0] if loss_trace else None,
        "final_loss": loss_trace[-1] if loss_trace else None,
        "delta_out": adapter.delta_out.detach().clone(),
        "delta_in": adapter.delta_in.detach().clone(),
        "delta_out_l2": float(adapter.delta_out.detach().norm().item()),
        "delta_in_l2": float(adapter.delta_in.detach().norm().item()),
        "invariance": inv,
    }


@torch.no_grad()
def verify_cache_reuse_and_rebuild_parity(
    adapter: PairedSwitchAdapter,
    *,
    prefix_token_ids: list[int],
    continuation_token_ids: list[int],
    delta_out: torch.Tensor,
    delta_in: torch.Tensor,
    numerical_tol: float = 1e-4,
) -> dict[str, Any]:
    """Section 3A verification:
    1. Prefill prefix with original weights (helper absent from prefix).
    2. Install edited (delta_out, delta_in).
    3. Verify historical K/V cache is bit-exact identical to full prefix rebuild.
    4. Verify switch-boundary scoring uses NEW output row (not stale logits).
    5. Verify cached forward-only continuation matches full from-scratch rebuild
       from identical concatenated IDs within declared numerical tolerance.
    """
    if adapter.helper_token_id in prefix_token_ids:
        raise AssertionError("Helper token appeared in prefix")
    if adapter.helper_token_id not in continuation_token_ids:
        raise AssertionError("Continuation must include <H0> to test post-switch input reuse")

    # 1. Prefill once under original weights.
    adapter.set_deltas(None, None)
    prefill = adapter.prefill_prefix(prefix_token_ids)

    # 2. Switch forward-only: install new output & input row deltas.
    adapter.set_deltas(delta_out, delta_in)
    fresh_boundary_logits = adapter.score_switch_boundary(prefill)

    # Confirm stale logits were NOT reused (h0 logit changed by h_last @ delta_out, other rows 0 diff).
    h0 = adapter.helper_token_id
    boundary_diff = (fresh_boundary_logits - prefill.stale_logits).abs()[0]
    other_mask = torch.ones_like(boundary_diff, dtype=torch.bool)
    other_mask[h0] = False
    boundary_other_max_diff = float(boundary_diff[other_mask].max().item())
    boundary_h0_actual_shift = float(
        (fresh_boundary_logits[0, h0] - prefill.stale_logits[0, h0]).item()
    )
    expected_h0_shift = float(
        torch.matmul(
            prefill.last_hidden_state.to(torch.float32),
            delta_out.to(device=prefill.last_hidden_state.device, dtype=torch.float32),
        ).item()
    )
    boundary_h0_shift_err = abs(boundary_h0_actual_shift - expected_h0_shift)

    # 3. Full prefix rebuild WITH edited (delta_out, delta_in) -> compare historical K/V bit-exact.
    inp_prefix = torch.tensor([prefix_token_ids], dtype=torch.long, device=adapter.device)
    pos_prefix = torch.arange(len(prefix_token_ids), dtype=torch.long, device=adapter.device).unsqueeze(0)
    rebuild_prefix = adapter.model(input_ids=inp_prefix, position_ids=pos_prefix, use_cache=True)

    orig_kv = extract_kv_pairs(prefill.past_key_values)
    reb_kv = extract_kv_pairs(rebuild_prefix.past_key_values)
    max_kv_diff = 0.0
    for (k1, v1), (k2, v2) in zip(orig_kv, reb_kv):
        max_kv_diff = max(
            max_kv_diff,
            float((k1 - k2).abs().max().item()),
            float((v1 - v2).abs().max().item()),
        )
    boundary_vs_rebuild_diff = float(
        (fresh_boundary_logits - rebuild_prefix.logits[:, -1, :]).abs().max().item()
    )

    # 4. Cached continuation vs full rebuild of prefix + continuation.
    cached_cont_logits, _ = adapter.forward_from_cache(
        prefill.past_key_values,
        start_pos=len(prefix_token_ids),
        new_token_ids=continuation_token_ids,
    )
    full_ids = prefix_token_ids + continuation_token_ids
    inp_full = torch.tensor([full_ids], dtype=torch.long, device=adapter.device)
    pos_full = torch.arange(len(full_ids), dtype=torch.long, device=adapter.device).unsqueeze(0)
    rebuild_full = adapter.model(input_ids=inp_full, position_ids=pos_full, use_cache=False)
    rebuild_cont_logits = rebuild_full.logits[:, len(prefix_token_ids) :, :]

    cont_max_abs_diff = float((cached_cont_logits - rebuild_cont_logits).abs().max().item())

    passed = (
        max_kv_diff == 0.0
        and boundary_other_max_diff <= numerical_tol
        and boundary_h0_shift_err <= numerical_tol
        and boundary_vs_rebuild_diff <= numerical_tol
        and cont_max_abs_diff <= numerical_tol
    )
    return {
        "declared_numerical_tol": numerical_tol,
        "historical_kv_max_abs_diff": max_kv_diff,
        "boundary_non_h0_max_abs_diff": boundary_other_max_diff,
        "boundary_h0_actual_shift": boundary_h0_actual_shift,
        "boundary_h0_expected_shift": expected_h0_shift,
        "boundary_h0_shift_error": boundary_h0_shift_err,
        "boundary_vs_rebuild_max_abs_diff": boundary_vs_rebuild_diff,
        "continuation_vs_rebuild_max_abs_diff": cont_max_abs_diff,
        "stale_logits_avoided": abs(boundary_h0_actual_shift) > 0.0 or abs(expected_h0_shift) == 0.0,
        "passed": passed,
    }


def _kl_div_from_logits(logits_p: torch.Tensor, logits_q: torch.Tensor) -> float:
    log_p = F.log_softmax(logits_p.detach().cpu().to(torch.float64), dim=-1)
    log_q = F.log_softmax(logits_q.detach().cpu().to(torch.float64), dim=-1)
    p = log_p.exp()
    return max(0.0, float((p * (log_p - log_q)).sum(dim=-1).mean().item()))


@torch.no_grad()
def run_forced_call_check(
    adapter: PairedSwitchAdapter,
    *,
    prefix_token_ids: list[int],
    pre_call_tokens: list[int],
    forced_operands_and_body_tokens: list[int],
    forced_verifier_response_tokens: list[int],
    shared_delta_out: torch.Tensor,
    adapted_delta_in: torch.Tensor,
) -> dict[str, Any]:
    """Section 3B forced-call isolation check:
    - Copy ONE exact output row (`shared_delta_out`) into BOTH branches.
    - Toggle ONLY the input embedding (`delta_in = 0` vs `delta_in = adapted_delta_in`).
    - Compare next-token scores immediately BEFORE `<H0>` is consumed: ANY
      non-zero pre-call difference FAILS the fixture.
    - Force the exact same `<H0>` call, operands, and verifier response in both
      branches, then compare subsequent scores and top-1 decisions.
    """
    h0 = adapter.helper_token_id
    if h0 in prefix_token_ids or h0 in pre_call_tokens:
        raise AssertionError("Helper token ID may not appear before the forced call boundary")

    # Prefill prefix once under original weights (shared cache base).
    adapter.set_deltas(None, None)
    prefill = adapter.prefill_prefix(prefix_token_ids)

    def _run_branch(delta_in_vec: torch.Tensor | None) -> dict[str, torch.Tensor]:
        adapter.set_deltas(shared_delta_out, delta_in_vec)
        if pre_call_tokens:
            pre_logits_seq, cache_pre = adapter.forward_from_cache(
                prefill.past_key_values,
                start_pos=len(prefix_token_ids),
                new_token_ids=pre_call_tokens,
            )
            pre_call_logits = pre_logits_seq[:, -1, :]
            pos = len(prefix_token_ids) + len(pre_call_tokens)
        else:
            pre_call_logits = adapter.score_switch_boundary(prefill)
            cache_pre = clone_kv_cache(prefill.past_key_values)
            pos = len(prefix_token_ids)

        # Force exact same <H0> token, operands, and verifier response.
        forced_seq = [h0] + list(forced_operands_and_body_tokens) + list(forced_verifier_response_tokens)
        post_logits_seq, _ = adapter.forward_from_cache(
            cache_pre,
            start_pos=pos,
            new_token_ids=forced_seq,
        )
        return {
            "pre_call_logits": pre_call_logits,
            "post_h0_logits": post_logits_seq[:, 0, :],
            "post_operands_logits": post_logits_seq[:, len(forced_operands_and_body_tokens), :],
            "post_verifier_logits": post_logits_seq[:, -1, :],
        }

    branch_orig = _run_branch(None)
    branch_adapt = _run_branch(adapted_delta_in)

    pre_diff = float(
        (branch_orig["pre_call_logits"] - branch_adapt["pre_call_logits"]).abs().max().item()
    )
    post_h0_diff = float(
        (branch_orig["post_h0_logits"] - branch_adapt["post_h0_logits"]).abs().max().item()
    )
    post_ops_diff = float(
        (branch_orig["post_operands_logits"] - branch_adapt["post_operands_logits"]).abs().max().item()
    )
    post_ver_diff = float(
        (branch_orig["post_verifier_logits"] - branch_adapt["post_verifier_logits"]).abs().max().item()
    )
    post_ver_l2 = float(
        (branch_orig["post_verifier_logits"] - branch_adapt["post_verifier_logits"]).norm().item()
    )
    post_ver_kl = _kl_div_from_logits(
        branch_orig["post_verifier_logits"], branch_adapt["post_verifier_logits"]
    )
    top1_orig = int(branch_orig["post_verifier_logits"].argmax(dim=-1).item())
    top1_adapt = int(branch_adapt["post_verifier_logits"].argmax(dim=-1).item())

    fixture_passed = pre_diff == 0.0
    input_effect_isolated = fixture_passed and post_h0_diff > 0.0 and post_ver_diff > 0.0

    return {
        "shared_output_row_copied_exact": True,
        "pre_call_max_abs_diff": pre_diff,
        "fixture_passed": fixture_passed,
        "post_h0_max_abs_diff": post_h0_diff,
        "post_operands_max_abs_diff": post_ops_diff,
        "post_verifier_max_abs_diff": post_ver_diff,
        "post_verifier_l2_diff": post_ver_l2,
        "post_verifier_kl_div": post_ver_kl,
        "post_verifier_top1_orig": top1_orig,
        "post_verifier_top1_adapt": top1_adapt,
        "post_verifier_top1_changed": top1_orig != top1_adapt,
        "input_effect_isolated": input_effect_isolated,
        "free_search_benefit_established": None,
    }
