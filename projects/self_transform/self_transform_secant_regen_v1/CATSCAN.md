# CATSCAN: Secant quasi-newton heredity and neural regeneration

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Test whether an affine-invariant secant-trust neural weight transformer retains improvements across four cold-process generations, improves proposals over fixed proposers with matched state, preserves heredity via weight-free neural regeneration, and beats calibrated conventional optimizers.

## Authority

- Owns the CPU-only `self_transform_secant_regen_v1` operator, autodiff tape, subprocess worker, frozen selection/confirmation contracts, and analysis scripts.
- Does not modify prior `self_transform_*` directories, `reconfiguration/` studies, or Doppler runtimes.

## Scope

- Applies to candidate selection, sealed confirmation, unit contracts, and reporting under `projects/self_transform_secant_regen_v1/`.

## Contracts

- Input: Pinned evidence rules from [Gamma research projects](../CATSCAN.md), frozen JSON protocols, and a strict loss-and-gradient oracle charging failed attempts, gradients, regeneration, and selection.
- Output: Hashed float64 serialized artifacts, weight-free behavioral regeneration transcripts, subprocess receipts, and statistical gate evaluations.

## Invariants

- Every update step across learned and conventional arms consumes one charged loss-and-gradient evaluation with failed attempts still billed.
- Evolving and fixed proposers are compared under identical retained-state regimes (`reset`, `retain`, and same-parent/same-state paired splits).
- Neural regeneration transmits only input-output behavioral probes across the OS process boundary and charges all distillation steps.
- Selection and confirmation populations remain disjoint; confirmation executes once after sealing the selected rule hash.

## Acceptance

- [Unit and isolation tests](test.mjs) verify failed-attempt charging, autodiff parity, affine invariance, weight-free neural regeneration, worker parity, and budget equality.

## Non-goals

- Claiming strict source-printing quines, GPU/LLM transfer, or unbounded recursive self-improvement.

## Freedom

Any pure CPU implementation that preserves these contracts, frozen protocols, and acceptance checks.
