# Native forward boundary for fixed P/E

**The new forward boundary matches every retained native logit and probability
bit-for-bit on both declared fixtures.** It freshly exports current model tensors
and executes the unchanged pinned predictor. No training or parameter update
occurred. This corrects the values entering the objective; it is not a compression
gain or a proof about the backward approximation.

**Follow-through completed:** the
[matched data-only/joint-cost experiment](fx2_matched_training_20260920.md)
already used this boundary. Native training-window loss improved, but native
archives worsened. Its selected joint-cost checkpoint saves fixed model bytes
and remains below scale admission. The earlier next-comparison recommendation
has been fulfilled; no repeat is implied by this report.

| Fixture | Scored positions | P loss, bits | E loss, bits | E minus P, bits | Corrected/native discrepancy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Synthetic, 8 input rows | 7 | 104.881477 | 111.209216 | +6.327739 | 0 |
| Retained native, 2,048 input rows | 2,043 | 3,329.616042 | 4,724.549235 | +1,394.933194 | 0 |

P was re-exported and rerun after E on each fixture. All 2,528,880 float32 values
across the six calls match the earlier independent native replay. Each call's
434 exported tensor identities match the original native decoder. P's exported
weight identity repeats exactly and differs from E's, excluding stale checkpoint
reuse in these calls. Every call starts with fresh native recurrent state and
preserves the fixture's actual reset markers.

E still has worse neural loss than P. The previous attribution's -23.538952-bit
real-input discrepancy is eliminated at the new forward boundary; it has not
become an archive saving. The earlier Torch reference and measured archives remain
unchanged historical evidence. No final-mixer or full-corpus measurement occurs.

## Implementation and gradient boundary

[NativeForward](../src/gamma_enwiki9/adapters/fx2_native_forward.py) receives an
explicit native binary identity, workspace, current model, export template,
tokens, reset markers and FP16 priors. It exports the current tensors on every
call, then runs a fresh bounded native child. Its inputs do not include captured
predictions or intermediate values. The validator reads expected outputs only
after the forward call. Original native sources are authenticated and unmodified.

Both logits and probabilities come from native execution. The loss uses actual
native truth probabilities, excludes piece-ending and final unpaired rows, and
rejects a different token population. This is a neural-head loss, not the final
mixer or a rounded archive-size objective. Bitwise equality is required for all
forward values. An absolute 1e-10-bit allowance applies only to FP64 summation
order; the measured P/E discrepancy is exactly zero here.

The backward path remains deliberately separate. The existing CPU reference
supplies a **whole-model surrogate Jacobian**. Torch's softmax Jacobian is evaluated
at native logits; forward probability values remain the actual native probabilities.
The custom autograd function returns native values directly and routes only the
adjoint into the surrogate. Subtracting and re-adding values could lose forward
bits through cancellation; focused tests cover that case and signed zero.

This is an approximate gradient, not native differentiation, an exact derivative
of quantization/archive size, or a claim that internal Torch states now match.
Two synthetic backward checks reach 429 finite, nonzero parameter-gradient tensors
for each of P and E. State hashes remain unchanged; there are zero optimizer
updates. Real-input evaluation performs no backward pass. Gradient usefulness
for subsequent optimization is unmeasured.

## Frozen scope and evidence

Candidate `fx2_native_forward2048_q0_v1`, owner `codex-native-forward-20260919`,
was published before execution at `276eb1a37`. The
[plan](../operations/provenance/fx2_native_forward2048_q0_v1_plan.json),
[experiment](../operations/adaptive/experiments/fx2_native_forward2048_q0_v1.json),
[closure](../operations/provenance/fx2_native_forward2048_q0_v1_closure.json), and
[synthetic preflight](../operations/provenance/fx2_native_forward_synthetic_20260919.json)
bind the correction. The real population is the same exposed 2,048 modeled-token
rows as the earlier attribution, with 2,043 paired truth positions. It is not
2,048 raw corpus bytes, an unseen confirmation, or a larger population.

The [validator](../src/gamma_enwiki9/adapters/fx2_forward_validation.py) uses the
existing bounded numerical gate and a thin tool entrypoint. Execution, evidence,
and scientific authority remain separate. This implementation preserves the
component intent and changes no codec, framework authority, or prize target.

[Comparison](../results/fx2_native_forward2048_q0_v1/comparison.json),
[terminal analysis](../results/fx2_native_forward2048_q0_v1/terminal.json),
[artifact manifest](../results/fx2_native_forward2048_q0_v1/artifacts.json),
[terminal arm index](../results/fx2_native_forward2048_q0_v1/terminal-index.json), and
[validated reflection](../operations/adaptive/reflections/20260920T025512Z_a4dd4d31c3.json)
retain the result. All 160 execution artifacts were rehashed. Six diagnostic
rows are recorded in the existing run ledger, with archive, inversion and
full-score fields null. No second registry or queue was created.

Job `20260920T025512Z_a4dd4d31c3` completed in 38.3005 seconds under CPU 3,
a 4 GB resident cap, 1 GB scratch cap, no swap and a 1,800-second wall stop.
Peak cgroup memory was 1,469,566,976 bytes; sampled peak allocated scratch was
318,197,760 bytes. All guards and owned cleanup passed. Timing is diagnostic.
The architecture group passed 143 tests and 54 subtests; both focused forward/
adjoint tests passed. Compilation and module import checks passed.

## Completed next comparison

The forward-value prerequisite is satisfied for this profile and fixed P/E
population. Candidate `fx2_matched_train250k_q0_v1` subsequently compared data-only
and joint model-cost development training with the same parent, windows,
initialization, update budget, normalization and selection rules, without metadata.
Its fresh packed checkpoints and finite archives are retained in the linked
report. Neither the histogram surrogate nor training-window loss supplied a
full-corpus gain. New checkpoint exports still require fresh native evaluation;
the [remaining question](fx2_matched_training_20260920.md#current-research-priority)
is the failure of measured training-window gains to improve archives.

P/E and retired metadata checkpoints remain intact. The 96,000,000-byte target
and 95,000,000-byte stretch remain unchanged; this gate earns zero score credit.
