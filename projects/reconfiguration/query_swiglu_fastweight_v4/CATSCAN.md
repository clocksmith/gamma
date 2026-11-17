# CATSCAN: Closed-form reversible per-layer MLP LoRA reconfiguration study (v4)

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Test whether a forward-only, closed-form reversible per-layer MLP `down_proj` low-rank weight update (`W_l(alpha) = W_l + alpha * B_l A_l`) compiled from a support context without gradient steps or string heuristics (a) retains domain-specific routing/classification capability when the support prompt is completely removed at query time (`Regime A`, with bit-exact base restoration at `alpha = 0` and after adapter detachment on quantized `Q4_K_M` WebGPU), and (b) competes honestly against prompt-present baselines including `Grave et al. (2017)` continuous cache / prompt `kNN-LM`, `Shi et al. (2024)` 2-pass Context-Aware Decoding (`CAD`), chat-templated decoding, and lexical/regex retrieval (`Regime B`) across `N = 96` non-copy tasks per stock model (`Gemma-3-270M-IT` and `Qwen3.5-0.8B`).

## Authority

- Owns `projects/reconfiguration/query_swiglu_fastweight_v4/` protocols, evaluators, non-copy task generators, unit tests, receipts, and reporting.
- Consumes `gamma/fastweight/` (`compile_closed_form_layer_lora` / `compileClosedFormLayerLoRA`) with `enable_string_heuristics = False` and leaves sealed `v1`, `v2`, and `v3` receipts untouched.

## Scope

- Two-commit pre-registration: Commit 1 freezes the closed-form per-layer `down_proj` LoRA solver, baseline harnesses, and `protocol_v4.json` before `tasks_v4.py` (`seed = 1040001`) is created or executed in Commit 2.
- Literature-grounded comparison positioned explicitly as an engineering synthesis of continuous caches (`Grave et al., 2017`), `kNN-LM` (`Khandelwal et al., 2020`), Context-Aware Decoding (`Shi et al., 2024`), implicit contextual MLP rank-1 updates (`Dherin et al., 2025`), and closed-form fast weights (`FAAST, 2026`).
- Unpooled per-model exact two-sided McNemar inference (`N = 96` tasks per model, never pooling across models to inflate sample size).

## Contracts

- Input: [Reconfiguration charter](../CATSCAN.md), frozen `gamma/fastweight/` (`v4`) solver, locally provisioned stock Doppler WebGPU models (`Gemma-3-270M-IT`, `Qwen3.5-0.8B`), and untouched confirmation seed `1040001`.
- Output: `protocol_v4.json`, `doppler_gemma3_270m_v4.json`, `doppler_qwen35_08b_v4.json`, and honest per-regime documentation in `README.md`.

## Invariants

- Frozen base weights remain bit-for-bit unchanged; `max_abs_logit_diff(zero_lora, base) == 0.0` on every task and `max_abs_logit_diff(reverted_after_hotswap, base) == 0.0` after specialty hot-swap and detachment.
- Zero regex, BPE-healing, or hop-continuation string shortcuts inside the closed-form LoRA arm.
- Wall-clock `setup_ms` starts before GPU support-activation capture and buffer readback.
- Standalone lexical/regex lookup baseline scores `<= 50%` on the `N = 96` confirmation tasks to verify genuine non-copy semantic/compositional structure.

## Acceptance

- [Cross-engine parity tests](../../../tests/test_fastweight_parity.py), [pre-registered protocol lock](protocol_v4.json), and `test_v4.py` non-copy verification pass before confirmation receipts are sealed.

## Non-goals

- Claiming theoretical novelty over `Grave et al. (2017)`, `Shi et al. (2024)`, or `FAAST (2026)`, or auto-downloading unprovisioned model weights.

## Freedom

- Grouping unseen queries under explicit specialty support tables so per-specialty compilation cost and amortized per-query cost are both measured transparently.
