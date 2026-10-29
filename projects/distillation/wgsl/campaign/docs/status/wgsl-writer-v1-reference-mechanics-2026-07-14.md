# WGSL Writer v1 Reference Mechanics

The reference-only run passed after the writer policy, manifest, fixtures, and
harness were frozen and pushed in commit `34bf9cd4`.

## Result

| Gate | Result |
|---|---:|
| Complete-shader response contract | 3/3 |
| Compilation | 3/3 |
| Primary semantic variants | 9/9 |
| Semantic tasks | 3/3 |
| Historical-regression groups | 3/3 |

Each primary variant also ran a reversed-input dispatch and an
alternate-workgroup dispatch, for 27 total GPU dispatches. CPU-oracle numerical
agreement, prefix and suffix canaries, output padding, read-only inputs,
workgroup equivalence, and input-permutation equivalence all passed.

The runtime was headless Chromium WebGPU on the AMD RDNA3 adapter. The receipt
file is
`reports/training/wgsl-writer/doppler-wgsl-writer-v1/mechanics/reference.json`,
SHA-256
`a9ccfbefebce8827669dfb08a515699f8ae57e4902bf81d9edb88366099b99ab`,
with internal receipt hash
`c0bd72a9929d707e57485eedf589860ab3570352a4defc57b77d3b607fe0a0b1`.

## Boundary

This result qualifies the complete-shader verifier mechanics. It contains no
model output and establishes no writer capability. The visible tasks have no
calibration, selection, confirmation, or promotion authority.

The next permissible model action requires a separate diagnostic execution
policy that binds this exact reference receipt. That policy may compare the
unchanged Qwen 3.5 9B F16 base with the V13 seed-29 repair adapter only as a
zero-shot transfer diagnostic. Neither outcome may select or promote a writer.
