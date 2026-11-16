# CATSCAN: Scale-homogeneous subspace self-transformer

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Test whether a scale-homogeneous, block-decoupled active-subspace weight transformer achieves exact cold-process reproduction, retained fresh-task adaptation, and genuine proposer improvement separated from optimizer memory under separately frozen selection and confirmation protocols.

## Authority

- Owns the CPU-only `self_transform_subspace_v1` operator, subprocess worker, frozen selection/confirmation contracts, and analysis scripts.
- Does not modify prior `self_transform_*` studies, `reconfiguration/` studies, or Doppler production runtimes.

## Scope

- Applies to candidate selection, sealed confirmation, unit contracts, and reporting under `projects/self_transform_subspace_v1/`.

## Contracts

- Input: Pinned repository evidence rules from [Gamma research projects](../CATSCAN.md), frozen JSON protocols, and an eight-query scalar loss window per update step.
- Output: Cryptographically hashed float64 child artifacts, isolated subprocess execution receipts, and statistical gate evaluations.

## Invariants

- Every update step across learned and conventional methods consumes at most eight scalar loss evaluations with zero analytic derivatives or holdout access.
- Every confirmation proposal and held-out evaluation reconstructs its operator in a clean OS subprocess and verifies direct-execution parity.
- Selection seeds and confirmation seeds remain disjoint; confirmation executes once after sealing the selected candidate.
- Retained optimizer memory and evolved update rules are measured separately.

## Acceptance

- [Unit and isolation tests](test.mjs) verify oracle limits, scale homogeneity, artifact integrity, worker isolation, budget parity, and statistical checks.

## Non-goals

- Claiming strict source-printing quines, GPU acceleration, language-model transfer, or unbounded recursive self-improvement.

## Freedom

Any pure CPU implementation that preserves these contracts, frozen protocols, and acceptance checks.
