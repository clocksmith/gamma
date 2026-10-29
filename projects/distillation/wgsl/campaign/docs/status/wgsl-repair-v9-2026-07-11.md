# WGSL Repair V9 Status

This is the historical preflight and mechanics receipt. The missing-weights
blocker was resolved, and the primary seed-11 SFT result is recorded in
[WGSL Repair V10](wgsl-repair-v10-2026-07-12.md).

At freeze, V9 was harness-ready and blocked only on the primary Qwen 3.5 9B
weights. V9 itself is not a capability result.

The rejected V8 replay used Gemma 270M, four unique WGSL repairs duplicated to
eight rows, and prose-shaped outputs. V9 changes the experiment rather than
resuming that adapter:

- Qwen 3.5 9B is the primary student; Qwen 3.5 2B is an efficiency control.
- Qwen 3.6 27B is an already provisioned teacher and ceiling, not a substitute
  student.
- The response contract is replacement-only. The harness owns the source file
  and span; the model returns only replacement WGSL.
- The corpus builder requires the clean module to compile, the mutation to
  reproduce a compiler failure, and the reference replacement to restore the
  clean source.
- Kernel families, rather than individual mutation rows, choose the
  train/diagnostic/public split.

## Prepared corpus

The Radeon WebGPU verifier admitted 2,714 repairs from 345 distinct kernels:

| Source | Accepted rows |
| --- | ---: |
| Doppler | 1,823 |
| Zero-TVM at `32406c88acc201694df83a4e22df64bf4391d380` | 891 |

It discovered 348 shader files, compiled 347 clean modules, generated 2,973
mutations, accepted 2,714, and rejected 259. The split contains 2,130 training
rows, 285 diagnostic rows, and 299 public-test rows, with no kernel-family
overlap.

Three equal-size data lanes isolate external diversity:

| Lane | Doppler | External | Dataset hash |
| --- | ---: | ---: | --- |
| `anchor` | 1,200 | 0 | `2e2235c9fa7db5037c19d0c0f029bb49e9cc929bc2df5bc23ec395506b4941a8` |
| `external20` | 960 | 240 | `02ff49fede38256a4d891a13315cb2d2d102e626faf52671be88bd101fb84baf` |
| `random20` | 1,200 | 0 | `f00ff4254475513172ccc14c958a978154d812c2b646e448baa884a978f832d4` |

The corpus measures compiler repair, not complete semantic kernel correctness.
The sealed promotion suite must add dispatch, oracle, numerical, metamorphic,
and historical-regression checks.

## Optimizer surface

Gamma now exposes versioned JSON actions for completion-masked SFT, DPO,
grouped sampling, and clipped GRPO updates. Doppler verifies rollouts and emits
the six artifact classes required by the RLVR contract: reward vector,
verifier report, rollout group, policy update, policy checkpoint, and promotion
decision.

The group contract preserves prompt, completion, token IDs, completion masks,
policy and reference token log-probabilities, raw checks, scalarization,
group statistics, advantages, clipping configuration, KL configuration, and
policy hashes. Best-of-eight and DPO pairs are derived from the same frozen
groups used by the GRPO comparison.

## Runtime and blocker

The Gamma ROCm environment passed a BF16 matrix multiplication on Radeon 8060S
with Torch `2.12.1+rocm7.2`, HIP `7.2.53211`, and Transformers `5.13.1`. The
already present Qwen 3.6 27B snapshot passed model and runtime preflight against
the 65,945,612,288-byte device pool.

The primary preflight failed closed with
`model_not_provisioned:Qwen/Qwen3.5-9B@main`. The trainer does not download
model weights. Once that snapshot is provided, the next command can continue
through SFT, rollout verification, rejection sampling, DPO, and GRPO without a
change to the frozen model identity.

## Mechanics fixture

A one-step Gemma 3 270M fixture was used only to execute every optimizer path;
it is not a V9 student and cannot gate Qwen 3.5 9B. BF16 SFT completed with
loss `7.795848369598389`, then two on-policy samples preserved 96 rollout
tokens and both policy/reference log-probability streams. Neither sample
compiled, so the verifier retained zero accepted rejection rows and zero DPO
pairs from that rollout.

Separate frozen mechanics inputs then completed one DPO update at loss
`0.6911851167678833`. The verified zero-reward rollout completed one GRPO
update at loss `0.000003924668362742523`, recording the declared zero-variance
advantage behavior. These receipts prove the code paths execute; the zero
constructive passes are not a capability improvement.

The machine-readable receipt is
[wgsl-repair-v9-2026-07-11.json](wgsl-repair-v9-2026-07-11.json).
