# Fixed P/E numerical attribution

**Both implementations find E worse than P on the declared inputs.** The
numerical mismatch changes the size of the regression but does not reverse it.
No training, checkpoint selection, metadata addition or parameter update occurred.
The complete-byte target remains 96,000,000; this diagnostic earns zero score credit.

| Population | Scored predictions | Reference E minus P, bits | Native E minus P, bits | Native minus reference change, bits |
| --- | ---: | ---: | ---: | ---: |
| Synthetic tokens 0..7 | 7 | +7.457933 | +6.327739 | -1.130195 |
| First 2,048 retained native rows | 2,043 | +1,418.472146 | +1,394.933194 | -23.538952 |

On the real fixture, P reference/native losses are 3,319.942112/3,329.616042 bits;
E losses are 4,738.414257/4,724.549235 bits. These are sums of negative log2 of
actual FP32 neural truth probabilities using FP64 logarithms and summation.
They are not final-mixer losses, archive sizes, or an attribution of the earlier
22,938-byte 1MB archive regression. Parity alone cannot turn E into an improvement
on these measured populations. This does not reject retraining as a general idea.

## What was held fixed

Candidate `fx2_numeric_attribution2048_q0_v1`, published before execution at
`0317d2b4b`, binds the [plan](../operations/provenance/fx2_numeric_attribution2048_q0_v1_plan.json),
[experiment](../operations/adaptive/experiments/fx2_numeric_attribution2048_q0_v1.json)
and [original source closure](../operations/provenance/fx2_numeric_attribution2048_q0_v1_closure.json).
P/E checkpoint files and the pinned native source are unchanged. The reference
is the existing CPU adaptation used in development, with CPU Torch 2.11.0+cu130.
It retains its floating computation for this attribution; native semantics are
the deployment reference for a future correction.

Real inputs are modeled-token rows from the retained opening250KB native capture,
not 2,048 raw corpus bytes. The fixture overlaps development exposure, includes
the opening training window, and does not cover all four old training windows.
Both implementations receive identical tokens, FP16 priors and cold initialization.
End markers are rows 934,1179,1494,1813; starts are 0,935,1180,1495,1814.
End rows and the final unpaired row are excluded from the loss. Each intervention
replays the complete unchanged fixture, preserving reference batch shapes.

All 434 decoded tensors per checkpoint agree byte-for-byte across the native
loader, packed-file decoder and checkpoint export. Parameter state is unchanged
through evaluation. Instrumented versus uninstrumented native outputs agree
bitwise, as do instrumented versus uninstrumented reference outputs. These are
observer controls, not a claim of cross-implementation parity.

## Where values diverge

On the synthetic fixture, the first observed numeric difference for both models
is normalized embedding row0, coordinate0: native 0.4663049876689911 versus
reference 0.46630504727363586. Native normalization uses an explicit AVX FMA
sum-of-squares reduction and division; the reference calls Torch RMS normalization.
Exact weights and scales do not imply identical intermediate reductions.

P's first synthetic integer mismatch is row5, block3 MLP-down input634. Its
precursor is concrete: MLP-up's integer dot is 1300 in both implementations,
but its output is 0.307280570268631 native versus 0.30728062987327576 reference.
Native applies a folded scale to an integer dot; the reference accumulates
products of dequantized FP32 values. ReLU-squaring yields
0.09442134946584702 versus 0.09442138671875. With the same 0.0269775390625 scale,
the scaled values are 3.4999985694885254 versus 3.5 and the bins are 3 versus 4.
This localizes a computation mismatch before rounding; it does not indict ties-to-even.

E's first synthetic bin difference is row3, block10 forget-gate-up input97:
scaled 1.5 native versus 1.4999942779541016 reference, bins 2 versus 1.

The real fixture has different first bin boundaries:

| Checkpoint | Row / operation / coordinate | Scaled native / reference | Integer native / reference |
| --- | --- | --- | --- |
| P | 3 / block3 attention value input / 112 | 21.499998092651367 / 21.5 | 21 / 22 |
| E | 27 / block8 MLP-up input / 17 | -70.50000762939453 / -70.49999237060547 | -71 / -70 |

P first differs numerically at normalized embedding row0 coordinate2. E's first
bit difference there is only +0 versus -0; its first numerically unequal observed
value is block0 input coordinate0, after embedding/prior combination. The trace
separates float bit differences from integer bins: signed zero is one integer bin.
The full arrays retain quantizer inputs, scales, scaled values, bins, integer dots,
linear outputs, block boundaries, logits and probabilities. Reference integer dots
are reconstructed from its actual integers; Torch itself uses FP32 accumulation.

## What the interventions establish

The frozen limits were three cumulative first-value vector substitutions and
eight cumulative first-integer scalar substitutions, in separate families.
Only the first 64 input rows are traced. Native intermediates are diagnostic
substitutions in the reference, never hidden inputs to a deployed compressor.

On eight synthetic tokens, one integer substitution per checkpoint removes all
remaining traced bin differences. Maximum logit gaps fall from 0.768214 to
0.00000572 for P, and from 0.325458 to 0.00000477 for E. Small float differences remain.

On real inputs, two substitutions for P (rows3 and56) and three for E
(rows27,53,60) remove all remaining bin differences within the first64 rows.
The resulting maximum probability differences within those rows are below
0.00000072. However, full-fixture maximum logit gaps remain 1.771059 for P and
2.888628 for E. Later operations were not traced; full parity is unproved.
Reference losses after those substitutions are 3,323.083116 and 4,726.728775 bits.
These are intervention measurements, not corrected deployed model results.
Three first-value vector substitutions do not change the fixture losses or
remove the later bin divergence. Correcting the earliest float observation alone
therefore does not explain all later mismatch.

## Evidence and decision

[Comparison](../results/fx2_numeric_attribution2048_q0_v1/comparison.json),
[retained loss/trace analysis](../results/fx2_numeric_attribution2048_q0_v1/analysis.json),
[artifact manifest](../results/fx2_numeric_attribution2048_q0_v1/artifacts.json),
[terminal arm index](../results/fx2_numeric_attribution2048_q0_v1/terminal-index.json),
and [validated reflection](../operations/adaptive/reflections/20260920T023220Z_bded1a9e05.json)
retain the result. Four diagnostic arm rows are recorded in the existing run ledger;
archive, inversion and full-score fields remain null.

Job `20260920T023220Z_bded1a9e05` completed under CPU3, a 4GB resident cap,
1.5GB scratch cap, no swap and a 1,800-second wall stop. Guard elapsed time was
51.4202 seconds; peak cgroup memory 1,983,676,416 bytes; sampled peak scratch
457,801,728 bytes. All guards and owned cleanup passed. Timing is diagnostic.
All 405 execution artifacts were rehashed. The architecture pure group passed
143 tests and 54 subtests; the focused loss/comparator suite passed two tests.

Hold further training. The next implementation is a separately frozen correction
of the reference forward computation to pinned native normalization, rescaling
and state-update semantics, followed by fixed-checkpoint parity validation.
Do not change the competitive native parent, rounding rules, epsilon or tolerance
to conceal disagreement. Only then compare matched data-only and joint-cost
training without metadata, documenting any approximate backward rule as a
surrogate gradient and measuring actual packed files. Preserve P/E/M/S and the
prior measured archives throughout.
