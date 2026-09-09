# Final-parent residual counts, synthetic stage

Owner: `root_explore`. Identity: `fx2_final_residual_counts_v1`.
This is an implementation probe, with no corpus launch or compression credit.
Source and frozen corpus inputs must publish before any retained-trace or native
corpus comparison. HORIZON and MIDAS ownership and measured sources are unchanged.

The [opening delivery attribution](../operations/provenance/fx2_ratio_delivery_loss_attribution_v1_terminal.json)
found improved expert loss and worsened final loss. The
[direction certificate](../operations/provenance/fx2_final_direction_v1_terminal.json)
then excluded positive ideal gains on one fixed recorded correction path.
Independent reviewer `direction_certificate_review` found no defect in the
certificate, reproduced its integer interval sums, checked 29 file bindings and
passed six synthetic tests. That review did not regenerate corpus coefficients.

Deliberately selected discovery lenses 8 and 9: adapt against measured final
errors, with decoder-visible conditions and a matched causal control. Considered
alternatives were another paid final-head schedule (the KAIROS/PBVC package and
control failures argue against repeating it) and exact model packing (a separate
positive lane, which does not test the measured predictive mismatch).
The selected question is whether per-prefix final-parent observed/expected
counts pay when the old expert-level correction did not. This is conventional
calibration machinery, not a claim of algorithmic novelty or guaranteed gain.

Each of 255 binary byte-prefix contexts accumulates observed zero/one counts and
expected counts from the unchanged final parent Q16 probability. Both outcomes
have a 32-symbol prior. Their observed/expected ratios are floored to Q16 and
clipped to [1/4,4]. Multiply the original parent's odds by the ratio of these two
factors; round once to nearest-even and clamp to [1,65535]. Reuse the existing
integer delivery primitive. Update only after truth is decoded. Halve each
context's four counts after its 256th visit; no transmitted labels or schedule.
P returns its parent and does not learn. K learns exactly D's state but returns
the parent. D uses the correction. S updates observed counts with the opposite
binary label; parent expectations, actual prefix progression and budgets match.

This differs from historical residual XML keys and their additive correction
and regret gate, paid dyadic schedules, and the old expert's normalized 205-way
counts. No existing calibration layer is deleted: the opcode audit found that
its parent's SSE improved literal loss by 6615.574 bits on its own population.
It supplies no transferable FX2 saving.

The header stores every future-affecting field in 4612 little-endian bytes,
including pending parent probability, prefix, counters, visit phases and arm.
Checkpoint rejection is transactional. Tests cover exact rational predictions,
every serialized boundary, P/K behavior, K/D learned-state identity, pending
checkpoint replay, invalid inputs, decay and a deliberately favorable fixture.
These establish only component correctness, not a native codec roundtrip.

Development allowance: one fixed law, synthetic fixtures first; no parameter
sweep. Synthetic work uses CPU3, one compiler process, 512MiB address space,
60 CPU/elapsed seconds per phase, 180 seconds aggregate, 32MiB per file and
64MiB output scratch. A separately frozen opening250KB replay must bind original
probabilities/truths, independent inverse, deterministic repeats, all-state
synchronization and package costs before native implementation or confirmation.
Correctness failure, resource stop, loss and failed control separation remain
distinct. No confirmation population is used to select this implementation.
