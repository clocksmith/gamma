# WGSL Writer v3 reference qualification — 2026-07-18

## Decision

The four frozen WGSL Writer v3 mechanics-reference packages passed Chromium
WebGPU qualification on the identity bound below. Each package executed twice.
All eight runs compiled, dispatched or drew the declared pass sequence, matched
its numerical or raster oracle, reproduced the exact output hash, released all
tracked GPU resources, and closed the Chromium session without an error.

The campaign is now `reference_qualified_corpus_materialization_blocked`.
This closes the browser-executor mechanics gate only. It does not authorize
corpus materialization, training, checkpoint selection, seed confirmation,
promotion, a general WGSL-writer claim, or productization.

## Receipt

- Qualification receipt:
  `docs/status/wgsl-writer-v3-reference-qualification-2026-07-18.json`
  (`0ce2f83e7b8ab71f87a8a50ed623d4b34f8169856a8012d0eff5f3a126368f24`)
- Receipt self-hash:
  `ccba5c0305b3419a05464d61132e9bc330a9056b760aae5e9a91889e13422603`
- Pre-decision campaign policy hash bound by the run:
  `7634ba1258ac8da93deac558cd3e10165f773939fc23e061940a49b0837bc0f5`
- Qualified campaign policy:
  `tools/policies/wgsl-writer-v3-campaign-policy.json`
  (`2ff61659179ca5c9f15f580c21d052a92cd18113096d1a8ab29ed7a17bfdf4c1`)

The pre-decision policy kept `referenceQualification.status: not_run` while the
gate ran. The post-decision policy binds the passing receipt and changes the
status to `qualified`; this intentionally changes the campaign-policy hash.

## Bound runtime identity

- Host: Linux `7.0.0-22-generic`, x64
- Chromium: `145.0.7632.6`, headless
- WebGPU adapter: vendor `amd`, architecture `rdna-3`
- PCI identity: vendor `0x1002`, device `0x1586`
- Renderer: Radeon 8060S Graphics, RADV STRIX_HALO
- Driver: AMD `26.0.3`
- Backend contract: required `vulkan`, detected `vulkan`
- Chromium display/backend evidence: `ANGLE_VULKAN`,
  `(gl=egl-angle,angle=vulkan)`, `GaneshVulkan`
- Chromium feature evidence: WebGPU enabled, Vulkan enabled

The receipt also preserves the Chromium arguments, complete reported WebGPU
feature set, and reported adapter limits.

## Results

| Reference package | Kind | Runs | Output SHA-256 | Result |
| --- | --- | ---: | --- | --- |
| compute add-one | compute | 2 | `186c4353edfb0b61ae2f3e47643157914dcaf226c85718f6bccf6f8dfa252d13` | pass |
| procedural render | render | 2 | `44f73fde34e1fadead9689fd89315503c9262b6aa5f50b1cbaa0a3d02ba10cf8` | pass |
| indexed render | render | 2 | `4b06419528536a732dd5a90cea2a285208beaf5cd585c639b9626d60dfc04cda` | pass |
| compute-to-render | multi-pass | 2 | `3ccb9f6a76b04009d4a911517f5d1f4ae8ff6ebecc9aaf2081f1c3aba6f41fba` | pass |

Across the eight runs, all 24 tracked buffers/textures were destroyed and all
18 mapped-buffer lifecycles were paired with unmaps. Every validation,
out-of-memory, uncaptured-error, cleanup-error, and session-close error list was
empty.

## First failing boundary and fix

The unmodified qualification stopped on the first compute package. The compute
branch attempted to read render-only `viewport` and `scissor` state and returned
no output; oracle evaluation then threw instead of preserving the failed run.

The executor now applies viewport and scissor state only to render passes. The
qualification path also:

- converts oracle exceptions into task-level failure evidence;
- requires two policy-owned replays and exact output/pass-sequence agreement;
- makes the Vulkan backend contract explicit and fails on a backend mismatch;
- records Chromium, host, GPU, driver, adapter-feature, and adapter-limit identity;
- makes tracked map/unmap and destroy cleanup part of execution success; and
- records final Chromium-session cleanup before issuing the decision.

The campaign schema now requires a null receipt for `not_run` and a bound receipt
for `qualified`, and keeps executor/reference/campaign states aligned.

## Remaining boundary

The next gate is materializing the family-disjoint executable capability corpus
and its CPU numerical, CPU image, raster, cross-pass, bounds, metamorphic, and
historical-regression oracles. Depth/stencil, blending, indirect work, queries,
mipmapping, and multisampling remain outside the qualified mechanics envelope.

## Claim boundary

This evidence qualifies the four visible reference-package execution paths on
the bound AMD/Vulkan Chromium identity. It proves infrastructure mechanics, not
that Doppler or any model can author general shaders.
