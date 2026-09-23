# Frozen coverage and full-distribution preservation comparison

Status: prospectively frozen and queued; no outcome reported yet.
The question is whether broader supervision, preservation of P's distribution,
or their combination prevents the off-window damage measured in the
[closed attribution](fx2_training_trajectory_20260920.md).

Candidate `fx2_coverage_preservation250k_q0_v1`, owner
`codex-coverage-preservation-20260923`, uses the existing lab and native forward
boundary. [Plan](../operations/provenance/fx2_coverage_preservation250k_q0_v1_plan.json)
and [experiment](../operations/adaptive/experiments/fx2_coverage_preservation250k_q0_v1.json)
freeze the population, hypotheses, schedules, controls, resource limits and stop.
The 96M complete-byte target and 95M stretch are unchanged.

| Arm | Supervised distinct targets | Supervised exposures / updates | Preservation |
|---|---:|---:|---|
| P | None | 0 / 0 | Original comparator |
| N | 512 | 2,048 / 16 | None |
| B | 1,024 | 2,048 / 16 | None |
| R | 512 | 2,048 / 16 | Full distribution KL |
| BR | 1,024 | 2,048 / 16 | Full distribution KL |

Every child starts from P. All retain learning rate 0.00002, seed 923, the same
optimizer and norm clipping, architecture, frontend, statistical models, mixer
and coder. There is no model-description penalty in this factorial comparison.

N/R cycle the four original native piece starts four times. B/BR cycle eight
starts twice. Each starts at an authentic reset with 512 warmup rows and 128
supervised next-token targets. Four additional eligible starts are chosen by
position, not loss. All nine eligible starts supply preservation contexts; the
frozen sixteen-step modulo-nine schedule repeats the first seven twice and the
last two once. R/BR receive 2,048 additional replay exposures, 1,152 distinct
replay targets and sixteen additional native-forward/surrogate-backward calls.
Equal supervision is not equal computation; measured calls, CPU/wall time and
memory remain separate evidence.

The penalty is mean KL(P || child), in bits, with coefficient 1.0, over all 205
vocabulary probabilities on the replay targets. Native FP32 distributions are
explicitly normalized in FP64. Teacher outputs are detached and training-only;
each child computes its own state from the decoded prefix. The backward is the
existing approximate reference Jacobian, not exact native differentiation.

Common evaluation partitions are the disjoint membership intersections of
narrow supervision, broader supervision and preservation: 111 (512 targets),
011 (512), 001 (128), 000 (149,960 other neural targets), and 98 targets without a
preceding neural prediction. Complete trajectories never reset at partitions.
Neural and final integer-coder costs remain separate levels.

All five checkpoints receive fresh 250KB native encode, independent decode,
repeat and unobserved encode controls, plus actual packed-file measurements.
A child is eligible only if both payload and archive-plus-two-model cost beat P.
The lowest component total among eligible children is selected, with fixed tie
order N/B/R/BR. Only that child and P then replay the already exposed 1MB interval
as secondary development. No untouched-confirmation claim or post-result tuning
is permitted. If no child qualifies, retain P; no 1MB rescue run is selected.
No automatic larger run, new delivery package or prize credit follows.

The explicit training test group passes 13 checks, including full-distribution
sensitivity when truth probability is unchanged, zero identity KL/gradient,
teacher detachment, overlapping masks, native-forward and next-token boundaries,
and refusal to select a smaller model whose archive regresses. Existing CPU
Torch/numpy and the authorized isolated pytest installation are used; nothing
was installed. Execute training with the plan's pinned system Python; the pytest
path is supplied only for tests. The standard native observer has existing
synthetic/reset coverage and preserved original source identities.

This is a separately frozen, user-requested comparison justified by the measured
off-window loss. It does not reopen metadata, donor expansion or the closed
native parity work. Execution/evidence/adapter boundaries and historical bytes
are preserved. External papers and competition figures are not evidence inputs.
