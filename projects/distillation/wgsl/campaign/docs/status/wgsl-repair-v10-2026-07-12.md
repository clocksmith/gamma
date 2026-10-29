# WGSL Repair V10 Result

V10 establishes a narrow Qwen 3.5 9B capability result for family-disjoint
WGSL compiler repair. It does not establish semantic kernel correctness and it
does not promote the adapter.

The rejected V8 experiment used Gemma 3 270M, four unique repairs duplicated
to eight rows, one optimizer step, rank-4 LoRA on only `q_proj` and `v_proj`,
and a prose-shaped response contract. V10 instead evaluates a capable 9B
student after a compiler-verified replacement-only curriculum drawn from 190
Doppler kernels.

## Frozen paired result

Base and SFT policies sampled the same 299 public-diagnostic tasks eight times
in the same order, with identical per-sample seeds, temperature `0.8`, top-p
`0.95`, and a 64-token ceiling derived only from visible anchor targets.

| Metric | Qwen base | Seed-11 SFT | Effect |
| --- | ---: | ---: | ---: |
| Sample compile pass | 8.8211% | 88.8378% | +80.0167 points |
| Pass@1 | 8.3612% | 88.2943% | +79.9331 points |
| Pass@8 | 40.8027% | 90.3010% | +49.4983 points |
| Exact-reference samples | 0 / 2,392 | 2,124 / 2,392 | +2,124 |

The task-paired pass@1 comparison has 241 candidate-only wins, two base-only
wins, and exact McNemar `p = 4.194901838280833e-69`. Pass@8 has 157
candidate-only wins, nine base-only wins, and exact McNemar
`p = 4.794187446718929e-36`. These tests do not replace the cluster-aware
confidence interval required for promotion.

The source split is also positive:

| Source | Tasks | Base pass@1 | SFT pass@1 | Effect |
| --- | ---: | ---: | ---: | ---: |
| Doppler | 186 | 7.5269% | 98.3871% | +90.8602 points |
| Zero-TVM | 113 | 9.7345% | 71.6814% | +61.9469 points |

Zero-TVM at `32406c88acc201694df83a4e22df64bf4391d380` was not present in
the Doppler-only anchor lane, so the external-source result is not an
in-domain row replay. Kernel families do not overlap among training,
diagnostic, and public splits.

## Student and training

The student is `Qwen/Qwen3.5-9B` at exact revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Gamma trained the exact local
Transformers source in BF16 on Radeon ROCm. Separately, Doppler converted the
same source to a verified all-F16 RDRR artifact for WebGPU inference; the RDRR
conversion is not the training runtime.

The seed-11 SFT run used rank-32 LoRA with alpha 64 and dropout 0.05 on
`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, and
`down_proj`. It executed 800 microsteps with accumulation 8, or 100 optimizer
updates. The deterministic row order exposed the first 800 of 1,200 anchor
rows; those rows still cover all 129 anchor families, 190 kernels, and nine
mutation operators. The final loss was `9.179047992802225e-7`, mean loss was
`0.022453638633036378`, and all 100 optimizer-update rows recorded nonzero
gradient norms. Loss is diagnostic only; the paired compiler result is the
capability evidence.

## Verifier and evidence limits

Every one of the 4,784 base-plus-SFT samples was compiled separately through
`GPUShaderModule.getCompilationInfo()` in Chromium on AMD RDNA 3. Both sides
bind to verifier bundle
`81e4aea92507d8277754b66480cf1b695e4a91c5dc5723d0c9d73dff7e8959f8`
and runtime
`90b5aa881a018c12ceba56d5c7b15018e9f5b9f8fa6f07911419ac2bde4e7bbd`.

The SFT policy failed all eight samples on 29 tasks. Twenty-six of those tasks
come from Zero-TVM and three from Doppler. Twenty-seven groups were blocked by
the replacement-only response contract, usually empty output or repeated
`<think>` blocks. Eight public references exceed the frozen 64-token ceiling;
they remain in the denominator.

Compilation is necessary but not sufficient for an ML kernel. V10 has one
training seed, one data lane, and a public diagnostic that checks syntax and
mutation recovery. Seeds 29 and 47, the external20 and random20 controls,
dispatch/oracle/numerical/metamorphic tests, historical regressions, and the
sealed semantic suite are absent. The adapter is therefore not promoted.

The machine-readable receipt is
[wgsl-repair-v10-2026-07-12.json](wgsl-repair-v10-2026-07-12.json). V11 keeps
the 299 public tasks evaluation-only and derives DPO and GRPO updates from the
separate 285-task diagnostic split.
