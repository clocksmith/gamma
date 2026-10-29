# WGSL Repair V12 Controlled-Data Result

V12 completed all nine base-initialized Qwen 3.5 9B LoRA SFT runs and
all nine frozen diagnostic and public compiler evaluations. The targeted
`external20` lane passed the preregistered diagnostic selection gate and the
same rule reproduced descriptively on the public matrix. Under SAME-R this is
`seed_confirmed` compiler-repair evidence; the pointer-only cross-repository
register remains `mechanics_proven` because semantic guardrails are absent.

The machine-readable result is
[wgsl-repair-v12-2026-07-13.json](wgsl-repair-v12-2026-07-13.json).

## What was trained

- Student: `Qwen/Qwen3.5-9B` at revision
  `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Teacher: none. V12 is controlled data-centric SFT, not teacher distillation
  or hybrid distillation.
- Task: return only the repaired replacement span for a family-disjoint WGSL
  compiler mutation.
- Anchor: 1,200 Doppler repair rows.
- Treatment: 960 Doppler rows plus 240 pinned Zero-TVM repair rows.
- Random control: 1,200 Doppler rows after a count-matched, seeded random
  replacement operation.
- Replication: all three lanes at seeds 11, 29, and 47.
- Training: rank-32 LoRA, 1,200 microsteps, accumulation 8, 150 optimizer
  updates, BF16 through Gamma's PyTorch/ROCm executor.

Every run consumed 1,200 distinct rows exactly once under its recorded
seed/hash order. The finalizer rehashed all nine exported adapter files and
matched every byte digest to its export receipt.

## Adapter preservation

The three `external20` adapter files remain present on this machine and their
SHA-256 digests match the frozen result receipt. The separate
[adapter preservation manifest](wgsl-repair-v12-adapter-preservation-2026-07-13.json)
binds those files and their export receipts to the V12 result.
The executable local verification receipt is
[wgsl-repair-v12-adapter-preservation-verification-2026-07-13.json](wgsl-repair-v12-adapter-preservation-verification-2026-07-13.json).

All three exact byte streams are now published through Git LFS at Doppler
revision `9e33238db9a9d42bcf122967caf3563ee97d392c`. The manifest records one
revision-pinned URL per seed, and each remote response was streamed through
SHA-256 verification. Publication did not retrain, rewrite, or otherwise alter
V12. Preservation does not select a seed or establish inference parity.

## Diagnostic selection

The diagnostic matrix was completed before the public split was opened.
`external20` beat anchor at every seed, beat the random-control mean, and did
not regress the mean long stratum, so the frozen gate selected it.

| Lane | Mean diagnostic pass@1 | Mean long pass@1 |
| --- | ---: | ---: |
| Anchor | 97.895% | 50.000% |
| External20 | 99.298% | 90.000% |
| Random20 | 98.480% | not used by the long non-regression check |

## Public compiler result

The public set contains 299 tasks: 290 short tasks sampled with a 64-token
ceiling and nine long tasks sampled with a 640-token ceiling. Each policy has
eight samples per task. Short and long results are recombined over the original
299-task denominator.

| Lane | Mean pass@1 | Seed range | Mean pass@8 | Mean sample pass rate | Mean long pass@1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Anchor | 98.439% | 97.659%-99.331% | 99.331% | 98.648% | 59.259% |
| External20 | 99.443% | 99.331%-99.666% | 99.777% | 99.484% | 92.593% |
| Random20 | 98.885% | 98.328%-99.666% | 99.777% | 98.857% | 77.778% |

The treatment effects on the three-seed means are:

- `external20` versus anchor pass@1: **+1.003 percentage points**;
- `external20` versus random20 pass@1: **+0.557 percentage points**; and
- `external20` versus anchor long pass@1: **+33.333 percentage points**.

The already-frozen diagnostic rule also passes on the public outcomes:
`external20` beats anchor at every seed, beats the random-control mean, and
does not regress mean long pass@1. This is a replication description, not a
new post-outcome promotion threshold.

## Paired evidence

| Seed | Control | Control pass@1 | External20 pass@1 | Effect | External-only | Control-only | Exact McNemar p | Holm p |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | Anchor | 99.331% | 99.666% | +0.334 pp | 2 | 1 | 1.0000 | 1.0000 |
| 11 | Random20 | 98.328% | 99.666% | +1.338 pp | 5 | 1 | 0.2188 | 1.0000 |
| 29 | Anchor | 98.328% | 99.331% | +1.003 pp | 5 | 2 | 0.4531 | 1.0000 |
| 29 | Random20 | 99.666% | 99.331% | -0.334 pp | 1 | 2 | 1.0000 | 1.0000 |
| 47 | Anchor | 97.659% | 99.331% | +1.672 pp | 7 | 2 | 0.1797 | 1.0000 |
| 47 | Random20 | 98.662% | 99.331% | +0.669 pp | 4 | 2 | 0.6875 | 1.0000 |

None of the six per-seed control comparisons is significant after Holm
correction. The compiler task is near saturation, and the long-stratum estimate
comes from only nine tasks. Across seeds, external20 has 14 external-only versus
five anchor-only task outcomes and ten external-only versus five random-only
outcomes. Those pooled discordances are descriptive only: the same task IDs
repeat across seeds, so treating all seed-task pairs as independent would be
pseudoreplication.

## Evidence boundary

V12 supports a narrow conclusion: the Zero-TVM replacement policy produced the
best three-seed mean compiler-repair result, cleared the matched anchor and
random-control rule, and preserved that conclusion after the public split was
opened. It is stronger evidence for data curation than V10's single-seed SFT
result. V11 remains the separate one-seed GRPO optimizer result.

V12 does not establish semantic ML-kernel correctness. No sealed dispatch,
CPU-oracle, numerical, metamorphic, bounds, or historical-regression suite was
run. No adapter has passed PEFT-to-Doppler inference parity, no M3 mixed-Q4 lane
is accepted, no runtime performance was measured, and no adapter is promoted.

The next experiment must keep V12 frozen. Semantic evaluation, dense checkpoint
selection, GRPO from the selected SFT lane, and Doppler-native Qwen training
parity each require separate contracts and receipts.

The separate V13 semantic requirements are frozen in
[wgsl-repair-v13-semantic-design-2026-07-13.md](wgsl-repair-v13-semantic-design-2026-07-13.md).
Its readiness gate is blocked and grants no WGSL Doctor or shader-authoring
authority.
