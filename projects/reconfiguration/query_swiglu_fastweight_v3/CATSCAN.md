# CATSCAN: Key-verified associative and dynamic multi-hop SwiGLU fast-weight study (v3)

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Validate the production `gamma.fastweight` (`v3`) transformation across six unseen application and reasoning families (`seed=990001`, `R = 3` latency repeats), explanatory component ablations, and engine-faithful Doppler WebGPU Q4K transfer across `Gemma-3-270M-IT`, `Qwen3.5-0.8B`, and `Qwen3.5-2B`.

## Authority

- Owns `projects/reconfiguration/query_swiglu_fastweight_v3/` confirmation, ablation, and Doppler Q4K replication harnesses and receipts.
- Consumes `gamma/fastweight/` without mutating sealed `v1` or `v2` receipts.

## Scope

- Six unseen task families (`96` MPS confirmation tasks + `48`-task/model WebGPU replication), three causal ablations (`no_key_gate`, `no_dynamic_hop`, `no_loo_gate`), and `PyTorchEngine` runtime verification.

## Contracts

- Input: [Reconfiguration charter](../CATSCAN.md), frozen `gamma/fastweight/` implementation, and untouched seeds (`990001`, `995001`).
- Output: Protocol lock JSONs, confirmation/ablation receipt, cross-model Doppler Q4K receipts, and documentation.

## Invariants

- Base model weights remain unchanged.
- Doppler WebGPU reads true `lm_head` rows (including untied `Q4_K_M`) and full `h_last[0..T-1]`.
- Pre-registered gates require McNemar `p < 0.05` over `base` and strongest `matched_compute` control at `< 5.0%` setup cost.

## Acceptance

- [Unit tests](test_v3.py) and [parity tests](../../../tests/test_fastweight_parity.py) pass before confirmation runs.

## Non-goals

- Re-tuning against `v1` or `v2` confirmation seeds.

## Freedom

- Any reporting layout preserving raw per-task receipts and timing distributions.
