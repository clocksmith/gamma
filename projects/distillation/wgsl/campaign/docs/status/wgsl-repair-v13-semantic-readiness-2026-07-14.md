# WGSL Repair V13 Semantic Readiness

V13 has moved from a frozen design to admitted calibration and checkpoint
selection. It has not selected a seed, confirmed semantic capability, promoted
an adapter, or authorized WGSL Doctor.

The canonical current receipt is
`wgsl-repair-v13-semantic-readiness-2026-07-14.json`. The original
2026-07-13 V1 receipt remains immutable historical evidence.

## Corrected predecessor state

The hash-bound V12 portability receipt now passes for the base model and all
three external20 adapters at seeds 11, 29, and 47. V2 readiness consumes that
receipt directly rather than treating the V1 policy's historical blocker list
as permanent state. V1 evaluation remains available for exact replay.

The current readiness receipt therefore removes
`trainer_to_doppler_adapter_parity_absent`. It does not use the inspected
parity probe to choose a seed.

## Executable semantic mechanics

The reference-control harness ran three hand-authored qualification families
through Chromium WebGPU on AMD RDNA 3. All 3 tasks and all 9 primary dispatch
variants passed. Each task covered nominal, non-workgroup-multiple, and
boundary/tail shapes plus 32- and 64-lane workgroups.

Every dispatch matched a hash-bound float32 CPU oracle, preserved 16-element
prefix and suffix canaries, preserved output padding and read-only input bytes,
and cleared input-permutation and tiling-equivalence checks. The receipt is
`wgsl-repair-v13-reference-mechanics-2026-07-14.json` with file SHA-256
`d76d33a3bdcc42a9554eca1ce2b380bdff9f753765089c09e15e5a13e214f122`.

This is reference mechanics evidence. It is not model capability evidence and
has no selection authority.

## Frozen selection boundary

Calibration and checkpoint-selection populations are now family-, source-,
and input-seed-disjoint. Reference qualification passed 3/3 calibration tasks
and 6/6 checkpoint-selection tasks. Seed confirmation and one-use promotion
remain unmaterialized.

The frozen seed-selection policy is
`tools/policies/wgsl-repair-v13-seed-selection-policy.json` with SHA-256
`70644c10b6bf390f0acd091b7afd83f22ef2f41e257a02d32a21c1b2eace470f`.
It ranks semantic task passes, compiler passes, semantic variant passes, exact
reference completions, then the lowest numeric seed. The policy was frozen
before candidate evaluation.

## Current decision

`calibrationAllowed` and `checkpointSelectionAllowed` are true.
`seedConfirmationAllowed`, `promotionEvaluationAllowed`,
`semanticClaimAllowed`, `wgslDoctorAllowed`, and
`autonomousShaderAuthorAllowed` are false.

The remaining blockers are:

- no external20 seed has been selected under the frozen policy;
- the disjoint seed-confirmation population is unmaterialized;
- the one-use promotion population is unmaterialized.

The next admissible action is deterministic generation and semantic dispatch
for seeds 11, 29, and 47 on the frozen checkpoint-selection population,
followed by the frozen ranking rule. That selection will authorize only a later
seed-confirmation evaluation.
