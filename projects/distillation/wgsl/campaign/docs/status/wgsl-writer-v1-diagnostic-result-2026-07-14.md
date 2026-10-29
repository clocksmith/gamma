# WGSL Writer v1 Zero-Shot Diagnostic Result

Doppler now has a qualified complete-shader verifier, but neither tested model
initialization is a verified WGSL writer.

## Matched Result

| Initialization | Response contract | Compile | Semantic | Token-cap hits |
|---|---:|---:|---:|---:|
| Qwen 3.5 9B F16 base | 0/3 | 0/3 | 0/3 | 3/3 |
| V13 seed-29 repair adapter | 0/3 | 0/3 | 0/3 | 0/3 |

Both candidates received byte-identical prompts and generation settings, ran
once, and were evaluated without retries or output filtering. Neither produced
an exact reference shader.

The base model prefixed its outputs with a non-WGSL output-format envelope,
omitted the required `WORKGROUP_SIZE` override, reached the 768-token cap on all
three tasks, and failed compilation with an unexpected token.

The repair adapter produced shorter, shader-shaped outputs and did not hit the
token cap. All three still omitted the required override and declared storage
resources with `var<read>` or `var<read_write>`. Chromium rejected `read` as an
address space before dispatch.

The adapter therefore improved output length and surface shape but gained zero
response-contract, compilation, or semantic passes. The frozen primary metric
shows no repair-to-writer transfer.

Canonical result receipt:
`wgsl-writer-v1-diagnostic-result-2026-07-14.json`, SHA-256
`16fbd260763e9f3704cacc4b547599504dd98d5007d5d41ce1446576b620b94b`,
internal receipt hash
`2784912ee9810c1e82ef3f89ee03638ff59a466327aa7e62d5853fecce68c85c`.

## Boundary and Next Step

This is a three-task visible zero-shot diagnostic, not an estimate of general
writer quality. It selects no candidate and has no confirmation, promotion, or
product authority.

Do not tune either model against these visible mechanics tasks. The next writer
campaign needs a separate corpus of complete-shader specification/interface
pairs, followed by disjoint calibration, checkpoint-selection,
seed-confirmation, and one-use promotion populations. V13 seed 29 may remain an
initialization control, but its repair evidence cannot substitute for writer
training or writer evaluation.
