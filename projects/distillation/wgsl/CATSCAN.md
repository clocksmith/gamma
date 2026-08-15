# CATSCAN: WGSL distillation

Parent: [Distillation research](../CATSCAN.md)

## Target

Measure whether student models gain verifiable WGSL-generation capability under a frozen compile-and-test protocol.

## Authority

- Owns WGSL data, generation constraints, verifier protocol, and lane-specific evaluations.
- Does not own WebGPU runtime compatibility or general code-generation claims.

## Scope

- Applies to WGSL data, generation constraints, verifier protocol, and lane-specific evaluations.

## Contracts

- Input: Declared checkpoints, prompts, populations, and [lane protocol](README.md).
- Output: Generated shaders, verifier outcomes, metrics, and replayable receipts.

## Invariants

- Syntax, validation, and semantic execution outcomes remain distinguishable.
- Unverified text is not counted as a correct shader.
- Evaluation populations and compiler/runtime identity remain explicit.

## Acceptance

- Training and evaluation obey the frozen WGSL protocol and preserve exact verifier results.
- Evidence: [WGSL protocol tests](../../../tests/test_wgsl_training_protocol.py).

## Non-goals

- Treating WGSL benchmark success as broad browser or GPU-runtime compatibility.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
