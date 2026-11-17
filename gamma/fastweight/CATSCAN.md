# CATSCAN: Prompt-conditioned fast-weight runtime

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Provide an explicit, opt-in prompt-conditioned fast-weight session (`FastWeightSession`) for frozen causal language models across PyTorch and Doppler WebGPU without modifying base weights.

## Authority

- Owns `gamma/fastweight/` (`adapter.py`, `doppler_fastweight.mjs`) and its opt-in session contract used by `PyTorchEngine` and cross-engine callers.
- Does not alter default decoding when `fastweight` is disabled.

## Scope

- Single-prefill associative key verification, dynamic multi-hop decode-step resolution, and leave-one-out calibrated SwiGLU rule kernels from `(prompt_ids, embed_tokens, h_last, lm_head)`, with string/boundary heuristics explicitly gatable (`enable_string_heuristics`).
- Forward-only closed-form reversible per-layer MLP `down_proj` LoRA compilation (`compile_closed_form_layer_lora` / `compileClosedFormLayerLoRA`, `W_l(alpha) = W_l + alpha * B_l A_l`) and continuous-cache kNN output-logit baseline helpers across PyTorch and quantized Doppler WebGPU.

## Contracts

- Input: Tokenized prompt or support context, frozen embedding/unembedding/norm weights, and final hidden states or per-layer MLP `ffn_act` pre-activations.
- Output: Step-indexed sparse vocabulary logit deltas `(token_ids, delta_logits)` or reversible per-layer `down_proj` low-rank weight factors `(A_l, B_l)` controlled by scalar `alpha >= 0`, plus measured setup/memory telemetry.

## Invariants

- Base model weights remain bit-for-bit unchanged.
- Zero-scaled adapters produce `0.0` logit change relative to unmodified decoding.
- Python (`adapter.py`) and Doppler JS (`doppler_fastweight.mjs`) implementations agree numerically on identical inputs.

## Acceptance

- Evidence: [cross-engine parity and engine integration tests](../../tests/test_fastweight_parity.py).

## Non-goals

- Implicitly enabling fast-weights on engines without raw hidden-state and logit access.

## Freedom

- Vectorized CPU/GPU layouts that preserve numerical parity and `< 5%` setup overhead.
