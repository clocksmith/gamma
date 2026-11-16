# CATSCAN: Surprisal-ridge and shared-basis prompt transforms

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Test genuinely distinct training-free prompt-conditioned low-rank transforms (`unembed_surprisal_ridge`, `shared_hyperbasis_lora`, `prompt_nll_ridge_lora`) across fresh multi-token domains and model sizes (`0.5B` MPS to `2B` Doppler WebGPU) with wrong-context, random, zero, and matched-compute controls.

## Authority

- Owns task generators, transform operators, MPS/Doppler runners, unit tests, and reports under `projects/reconfiguration/surprisal_ridge_v1/`.
- The opt-in `--context-only` runners consume Gamma's reusable
  [state context compiler](../../../src/core/state_context.py) as a separate
  symbolic preprocessing comparison; they do not modify or qualify B1/B2 operators.
- Does not modify frozen `channel_gain`, `rotation_v1`, `contrastive_rank_one_v1`, `associative_delta_v1`, or Doppler runtime files.

## Scope

- Applies to training-free prompt-conditioned fast-weight evaluation, GPU-resident derivation/fusion checks when supported by quality evidence, and cross-domain/cross-size transfer.

## Contracts

- Input: Untouched frozen model artifacts, context-only prompt spans (excluding query answers), and frozen control schedules.
- Output: Multi-token decoded completions, exact restoration checks, setup/first-token/decode/memory timings, and paired quality receipts.

## Invariants

- Base weights remain bit-identical after every request; zero-factor adapters match base outputs.
- Transform derivation accesses only the prompt context span before the query suffix, never evaluation answers.
- Query-aware context preprocessing may inspect the query and context, never
  the expected answer. Its source-linked slice preserves replay semantics;
  unsupported inputs remain unchanged. It runs on every state case, independently
  of the weight-transform discrimination gates.
- Discriminative base gates execute before transform arms; trained-checkpoint baselines stay strictly separate.

## Acceptance

- [Unit and oracle tests](test_surprisal_ridge.py) verify deterministic multi-domain task oracles, context-only span boundaries, zero-adapter identity, and low-rank ridge math.

## Non-goals

- Claiming continual-pretraining gains as training-free or inferring general reasoning, RSI, or AGI.

## Freedom

Any implementation preserving these invariants, full cost accounting, and exact base-weight restoration.
