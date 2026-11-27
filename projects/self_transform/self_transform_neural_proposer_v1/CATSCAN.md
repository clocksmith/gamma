# CATSCAN: Self-applicable SwiGLU neural proposer heredity study

Parent: [Self-transform studies](../CATSCAN.md)

## Target

Test whether a multi-layer SwiGLU neural weight-proposer (`M_Phi`, 1,783 parameters) modifying its own weights across four cold-subprocess generations improves adaptation on unseen neural targets over its fixed initial self (`M_Phi_0`) and calibrated conventional optimizers (`SGD+Nesterov`, `AdamW`, `L-BFGS`) under matched budgets.

## Authority

- Owns the neural proposer, target generators, subprocess worker, baselines, tests, and receipts under `projects/self_transform/self_transform_neural_proposer_v1/`.
- Preserves prior `projects/self_transform_*` studies unchanged.

## Scope

- Four-generation self-application (`g = 0..4`), cold-process reconstruction plus weight-free behavioral self-regeneration, conventional calibration on disjoint tasks, and confirmation across three unseen neural target families.

## Contracts

- Input: [Gamma research projects charter](../../CATSCAN.md), disjoint meta-training/calibration/confirmation seeds, and strict forward-backward oracle counters.
- Output: Subprocess lineage receipts, per-seed confirmation tables, exact paired Wilcoxon/sign-test statistics, and full compute accounting.

## Invariants

- Every adaptation step on fresh cold targets starts with `state = None` and consumes an identical `B = 10` support forward-backward pass budget across learned and conventional arms.
- Self-improvement updates `Phi_g -> Phi_{g+1}` exclusively by applying `M_Phi_g` to its own layer activations and meta-gradients, never via an external optimizer.
- Behavioral self-regeneration transmits zero weight values across the OS process boundary and bills all probe/distillation compute.

## Acceptance

- [Unit tests](test_neural_proposer.py) verify cold-process isolation, zero state carry-over, exact budget parity, self-application, and weight-free regeneration.

## Non-goals

- Claiming source-code quines or open-ended LLM self-improvement beyond the measured neural target families.

## Freedom

- Any implementation preserving these boundaries, matched oracle budgets, and frozen evaluation splits.
