# CATSCAN: Frozen v2 SwiGLU fast-weight unseen confirmation study

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Execute a pre-registered, unseen six-family confirmation (`seed=970001`, 96 tasks) of the unit-standardized, LOO-NLL-calibrated SwiGLU fast-weight transform (`v2`) with symmetric canonical scoring and `R = 3` repeated latency measurements per task.

## Authority

- Owns frozen `v2` task generators, unit-standardized LOO-NLL transform, confirmation harness, and tests under `projects/reconfiguration/query_swiglu_fastweight_v2/`.
- Preserves `query_swiglu_fastweight_v1` code and receipts unchanged.

## Scope

- Six unseen task families (`firewall_rule_synthesis`, `artifact_checksum_registry`, `warehouse_tariff_schedule`, `biography_affiliation_memo`, `chained_alias_resolution`, `feature_flag_rollout`), seven arms, and `R = 3` timed passes on `base` and `focal_fastweight`.

## Contracts

- Input: [Gamma research projects charter](../../CATSCAN.md), symmetric scorer from `query_swiglu_fastweight_v1/score_receipts.py`, and pre-registered success gates written to `.protocol.json` before generation.
- Output: Confirmation JSON receipt with per-task outputs, `R = 3` repeated phase latencies (`mean`, `p50`, `p95`, `std`), bytes, and exact McNemar `p`-values.

## Invariants

- Context fast-weight derivation reads strictly `< context_len` with zero query-answer leakage.
- Success requires paired McNemar `p < 0.05` over both `base` and the strongest `matched_compute` control, plus mean `setup_ms < 5%` of `base`.

## Acceptance

- [Unit tests](test_v2.py) pass and all protocol SHA-256 locks match the sealed receipt.

## Non-goals

- Post-hoc tuning on `seed=970001` or modifying `v1` artifacts.

## Freedom

- Any implementation preserving these boundaries, frozen hashes, and repeated-timing contracts.
