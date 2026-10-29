# WGSL Repair V13 Seed-Confirmation Result

Selected external20 seed 29 passed the frozen, one-use semantic confirmation
gate. This establishes seed-confirmed replacement-only WGSL repair on the
constructed V13 population. It does not promote the adapter or establish a
general WGSL writer.

## Result

| Gate | Result |
|---|---:|
| Semantic tasks | 8/8 |
| Compiler passes | 8/8 |
| Primary semantic variants | 24/24 |
| Response-contract passes | 8/8 |
| Historical-regression passes | 8/8 |
| Exact reference completions | 7/8 |

The non-exact completion used the semantically equivalent WGSL literal `0.5f`
instead of `0.5` in the mean task. It compiled and passed every dispatch and
CPU-oracle comparison.

The model ran exactly once after the balanced population, evaluation policy,
and passing reference receipt were committed and pushed. No prompt, sampler,
completion, or task was edited or retried. The result binds the exact Doppler
F16 Qwen artifact, seed-29 adapter bytes, deterministic token outputs, Chromium
WebGPU runtime, and all dispatch evidence.

Canonical artifacts:

- Result receipt: `wgsl-repair-v13-seed-confirmation-result-2026-07-14.json`,
  SHA-256
  `5195a50299e7054a49d5d176ce30f468e561f9870fe9890b404ee7b9ec352fc5`.
- Completion receipt: `seed29.completions.json`, SHA-256
  `a623a252a7d0914ce98d070ce2d456846e6ced8b0d0e59b36f3297aefeb2e242`.
- Semantic receipt: `seed29.semantic.json`, SHA-256
  `4e0a543e96989d6915d667a65d4a1c77b849b625690a89186ee7b2985ed98ebe`.
- Reference receipt: `wgsl-repair-v13-seed-confirmation-reference-2026-07-14.json`,
  SHA-256
  `26b826be2d194c521d95680d675a6c4bbaf62e13a5d2cd320248a38a89885b32`.

## Boundary

These are eight constructed, replacement-only tasks. The result does not cover
naturally occurring errors, cross-platform execution, complete shaders from
specifications, binding design, algorithm selection, or deployment. The
one-use promotion population remains unmaterialized, so semantic promotion,
WGSL Doctor, and autonomous shader authorship remain blocked.

Complete-shader writing must proceed as a separate experiment with a
specification-plus-dispatch contract as input and compilation, execution,
CPU-oracle, bounds, metamorphic, and regression verification as blocking output
gates.
