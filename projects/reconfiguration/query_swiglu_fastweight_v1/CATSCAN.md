# CATSCAN: Query-aligned SwiGLU fast-weight reconfiguration study

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Test whether a frozen single-prefill prompt-derived SwiGLU fast-weight transformation improves multi-token accuracy over `base`, `zero`, `wrong_context`, `random`, and `matched_compute` controls across unseen seeds, holdout task families, and model sizes (`270M` to `2B`) at low setup overhead.

## Authority

- Owns frozen candidate transforms, task generators, unit checks, PyTorch MPS and Doppler WebGPU evaluation harnesses, and receipts under `projects/reconfiguration/query_swiglu_fastweight_v1/`.
- Does not modify base model weights, Doppler runtime sources, or prior `projects/reconfiguration/*` artifacts.

## Scope

- Stage 1 selection (`seed=810001`), Stage 2 confirmation (`seed=920001` plus holdout families `seed=930001`), and cross-model transfer across `Gemma-3-270M-IT`, `Qwen3-0.6B`, `Qwen3.5-0.8B`, and `Qwen3.5-2B`.

## Contracts

- Input: [reconfiguration charter](../CATSCAN.md), pinned local checkpoints, and hashed protocol locks written before generation.
- Output: JSON receipts recording outputs, setup/first-token/decode/total latency, fast-weight bytes, RSS, and paired sign-test statistics.

## Invariants

- Context fast-weight derivation reads strictly tokens `< context_len` with zero query-answer leakage.
- Candidate selection freezes on `seed=810001` before any `seed=920001`, `seed=930001`, or cross-model run executes.
- `wrong_context` charges donor setup plus target inference; `matched_compute_base` spends equal-or-greater unmodified inference compute.
- Provenance of `Qwen3-0.6B-NHS` is disclosed separately from untouched `Gemma-3` and `Qwen3.5` checkpoints.

## Acceptance

- [Unit tests](test_query_swiglu_fastweight.py) pass and protocol hashes match sealed receipts.

## Non-goals

- Retuning after Stage 1 freeze, downloading weights, or claiming general reasoning gains beyond measured task families.

## Freedom

- Any implementation preserving these boundaries, frozen candidate hashes, and full cost accounting.
