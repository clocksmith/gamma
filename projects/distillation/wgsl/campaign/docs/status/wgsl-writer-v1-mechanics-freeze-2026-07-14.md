# WGSL Writer v1 Mechanics Freeze

Doppler now has an experimental complete-shader WGSL writer contract and an
executable semantic verifier. It does not yet have evidence that a model can
satisfy the contract.

This is a separate experiment, `doppler-wgsl-writer-v1`. V13 remains a
replacement-only repair experiment. Its seed-confirmation result may justify
testing the seed-29 adapter as an initialization, but no repair percentage or
receipt transfers into the writer claim.

## Frozen Input and Output

Each writer task provides:

- a natural-language arithmetic and safety specification;
- an explicit entry point, shader stage, override, binding, uniform-layout,
  dispatch, bounds, and output contract; and
- no broken source, repair span, or partial shader.

The response must contain one complete WGSL compute shader and nothing else.
Markdown fences, missing compute stages, missing `main`, missing required
overrides, compilation errors, dispatch errors, numerical mismatches, storage
corruption, shape failures, workgroup failures, metamorphic failures, and
historical regressions are blocking.

## Mechanics Qualification Set

The visible mechanics-only set contains three complete reference shaders:
vector addition, affine transformation, and clamping. Each runs at three shapes
including a single-element boundary and a non-workgroup-multiple tail, with two
workgroup sizes, reversed-input metamorphic execution, output canaries,
read-only input identity, CPU-oracle comparison, and deterministic receipts.

These tasks have `populationAuthority: none`. They may qualify the harness but
cannot calibrate, select, confirm, or promote a candidate.

## Frozen Boundaries

The policy freezes two possible future diagnostic initializations on the same
Qwen 3.5 9B F16 artifact: the unchanged base model and the V13 seed-29 repair
adapter. Neither is selected. Candidate inference is forbidden until a passing
reference-mechanics receipt is committed after this freeze.

All scientific populations remain unmaterialized and disjoint by contract:
calibration, checkpoint selection, seed confirmation, and one-use promotion.
No product command, autonomous writer claim, or deployment authority exists.

Canonical files:

- `tools/policies/wgsl-writer-v1-policy.json`
- `src/config/schema/wgsl-writer-experiment.schema.json`
- `tools/data/wgsl-writer-v1-mechanics.json`
- `tools/run-wgsl-writer-semantic-harness.js`
- `tools/lib/wgsl-writer-semantic-harness.js`
- `tools/lib/wgsl-semantic-harness.js`

The next permitted action is a reference-only Chromium WebGPU run. If that
passes and its receipt is committed, a separate diagnostic execution policy can
bind that receipt before either model initialization sees these tasks.
