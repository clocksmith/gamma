# CATSCAN: Prompt-conditioned fast-weight runtime

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Provide an explicit, opt-in prompt-conditioned fast-weight session (`FastWeightSession`) for frozen causal language models across PyTorch and Doppler WebGPU without modifying base weights.

## Authority

- Owns `gamma/fastweight/` (`adapter.py`, `doppler_fastweight.mjs`) and its opt-in session contract used by `PyTorchEngine` and cross-engine callers.
- Does not alter default decoding when `fastweight` is disabled.

## Scope

- Single-prefill associative key verification, dynamic multi-hop decode-step resolution, and leave-one-out calibrated SwiGLU rule kernels from `(prompt_ids, embed_tokens, h_last, lm_head)`.

## Contracts

- Input: Tokenized prompt with context boundary `c_len`, frozen embedding/unembedding matrices, and final hidden states.
- Output: Step-indexed sparse vocabulary logit deltas `(token_ids, delta_logits)` and measured setup/memory telemetry.

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
