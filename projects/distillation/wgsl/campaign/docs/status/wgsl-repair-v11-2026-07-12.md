# WGSL Repair V11 Optimizer Result

V11 establishes a narrow Qwen 3.5 9B GRPO-RLVR result for family-disjoint
WGSL compiler repair. One verifier-driven update improved the frozen seed-11
SFT policy on the untouched public diagnostic. The matched DPO lane
catastrophically regressed and is rejected. Neither result establishes semantic
kernel correctness or promotes an adapter.

## Frozen causal comparison

All optimizer data came from the 285-task diagnostic split. The 299-task
public split was evaluation-only and did not select a checkpoint, pair budget,
learning rate, or stopping rule. SFT, DPO, and GRPO used the same Qwen
`Qwen/Qwen3.5-9B` revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, replacement-only response
contract, eight-sample task groups, per-sample seeds, temperature `0.8`, top-p
`0.95`, and 64-token ceiling.

The public SFT reference was reverified under the same verifier bundle
`5ce6e5bf580307664a6a0afb95deb52aab3413e0e79d780a8c3862de6a0a252e`
and runtime
`90b5aa881a018c12ceba56d5c7b15018e9f5b9f8fa6f07911419ac2bde4e7bbd`
used for both optimizer candidates. The SFT parent policy is
`fcba6cbbfee3b52de597be8df7400ae601f6fdbc15989946da543cb299eebc87`.

## Diagnostic reward signal

The SFT policy sampled 2,280 diagnostic completions in 285 groups. Radeon
WebGPU verification produced:

| Group class | Groups | Group-relative update signal |
| --- | ---: | --- |
| All pass | 243 | none |
| All fail | 36 | none |
| Mixed pass/fail | 6 | constructive |
| Additional varying groups | 6 | five constructive, one exact-only |
| Total varying | 12 | 96 nonzero-advantage samples |

The constructive classifier therefore records 11 varying groups and one
exact-reference-only group. An exact-only difference is formatting preference,
not evidence that a different repair compiled. All-pass and all-fail groups
remain in the receipt but receive zero group-relative advantages.

The source split explains the signal concentration. All 145 Doppler groups
passed every sample. Among 140 Zero-TVM groups, 98 were all-pass, 36 were
all-fail, and six had mixed compile outcomes; pass@1 was 72.14% and pass@8 was
74.29%.

Derivation emitted 249 rejection-SFT rows, 11 ordinary on-policy DPO pairs,
and 36 reference-anchored corrective pairs for the all-fail groups. The
corrective pairs were excluded from V11 because their chosen responses are
off-policy compiler-qualified references. Mixing them into GRPO or ordinary
DPO would change the causal treatment.

## Optimizer mechanics

The DPO lane trained all 11 ordinary pairs for 400 steps. Its preference
margin moved from `-29.3499` at step 1 to `79.6811` at step 25 and `113.8226`
at step 400, while final loss fell to `1.1396e-5`. That is memorization of a
tiny pair bank, not capability evidence. The output policy is
`a2dbde4f0218ce641e41063462c20f3bda2b40fccc3cbae3c2fbad36823a1ace`.

The GRPO lane consumed only the 96 nonzero-advantage samples. It disabled LoRA
dropout, seed-shuffled the signal samples, accumulated 400 declared
microsteps against the frozen rollout policy, and made exactly one optimizer
update with zero stale-policy updates. Gradient norm was `40.5938`; final
loss was `0.8737`. The clipped objective, group-relative advantage formula,
and KL coefficient `0.02` are frozen in the V11 policy. The output policy is
`2019fd617a2f586b134e7d38893c1ebbd983c6d2bee2c61db8967a5581d88cfe`.

## Public paired result

Each policy generated 2,392 public samples. Every sample was compiled
independently through `GPUShaderModule.getCompilationInfo()` on AMD RDNA 3.

| Metric | SFT parent | DPO | GRPO | GRPO effect vs SFT |
| --- | ---: | ---: | ---: | ---: |
| Sample compile pass | 88.8378% | 36.1622% | 95.2759% | +6.4381 points |
| Pass@1 | 88.2943% | 36.7893% | 94.9833% | +6.6890 points |
| Pass@8 | 90.3010% | 53.8462% | 96.3211% | +6.0201 points |
| Exact-reference samples | 2,124 | 649 | 2,269 | +145 |
| Blocked samples | 216 | 0 | 11 | -205 |

GRPO added 20 task-level pass@1 wins with zero SFT-only wins. The exact paired
McNemar value is `p = 1.9073486328125e-6`. Pass@8 added 18 wins with zero
losses (`p = 7.62939453125e-6`). At sample level, GRPO added 154 passing
repairs with zero losses (`p = 8.758115402030098e-47`).

DPO lost 171 pass@1 tasks while gaining 17, an effect of -51.5050 points
(`p = 3.4521150515178205e-33`). Its low training loss is therefore a rejected
surrogate.

## Source and length effects

| Stratum | Tasks | SFT pass@1 | GRPO pass@1 | Effect |
| --- | ---: | ---: | ---: | ---: |
| Doppler | 186 | 98.3871% | 100.0000% | +1.6129 points |
| Zero-TVM | 113 | 71.6814% | 86.7257% | +15.0442 points |
| Short repair | 290 | 91.0345% | 97.5862% | +6.5517 points |
| Long repair | 9 | 0.0000% | 11.1111% | +11.1111 points |

The external source accounts for 17 of the 20 pass@1 gains and has zero
paired regressions. This is stronger than an in-domain formatting-only effect.
The long stratum remains unresolved: GRPO repaired only one of nine tasks, and
none of its 72 long samples exactly matched the references. V12's separately
frozen 640-token long decoder remains necessary.

## Evidence boundary and next gates

V11 is `capability_proven` only for one seed of public, family-disjoint WGSL
compiler repair under one sampler and one Radeon runtime. It is the first
primary Doppler RLVR capability result because verifiable rewards generated
group-relative advantages that drove the accepted policy update. It does not
show that GRPO beats SFT across seeds, that the generated shaders compute the
right values, or that the adapter is safe to ship.

The next optimizer work is a multi-seed confirmation and a semantic reward
curriculum with dispatch, CPU-oracle, numerical, metamorphic, bounds, and
historical-regression checks. DPO should return only with a disjoint
optimizer-selection partition and early checkpoints. Reference-anchored
corrective DPO remains a separate, preregistered off-policy lane.

The separate V12 experiment tests data composition from base initialization.
It must run the full anchor, external20, and random20 lanes without treating
this GRPO result as evidence that external SFT curation caused the gain.

The machine-readable receipt is
[wgsl-repair-v11-2026-07-12.json](wgsl-repair-v11-2026-07-12.json).
