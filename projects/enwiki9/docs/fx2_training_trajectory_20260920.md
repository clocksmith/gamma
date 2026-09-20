# Fixed P/A/J complete-trajectory attribution

**The training-position gains survive complete native replay; off-window losses
overwhelm them at both neural and final-coder measurement levels.** This closes
the requested attribution without new training, checkpoint selection, metadata,
confirmation-data access or changes to the codec's predictions.

[Comparison](../results/fx2_training_trajectory250k_q0_v1/comparison.json),
[terminal](../results/fx2_training_trajectory250k_q0_v1/terminal.json),
[independent verification](../results/fx2_training_trajectory250k_q0_v1/verification.json),
[validated reflection](../operations/adaptive/reflections/20260920T211447Z_85cfcf79b5.json).
The objective remains 96,000,000 complete bytes, with 95,000,000 stretch and an
unknown verified full-corpus score. This diagnostic earns no score credit.

## Population and coordinate checks

The fixed P/A/J packed checkpoints replay exposed raw[0,250000) through the
unchanged native frontend, predictors, mixer and coder. All 151,210 modeled-token
targets and 1,209,680 final coded bits are retained. Execution starts from the
original initialization and runs continuously; analysis partitions cause no resets.

The [frozen mask](../results/fx2_training_trajectory250k_q0_v1/mask.json) binds the
original token/reset identity. Four native piece starts are 0, 2611, 39712, 68859.
Each training window scores prediction rows [s+512,s+640), paired to target rows
[s+513,s+641). These are zero-based modeled-token coordinates, not raw offsets.
The exact target intervals are [513,641), [3124,3252), [40225,40353), [69372,69500).

There are 512 trained targets, 150,600 other neural-eligible targets and 98 targets
without a preceding native neural prediction (first target or first after a piece
ending). Neural cost is not imputed for the latter; all their 784 coded bits remain
in the final-coder totals. Their final costs can differ because the adaptive
predictors retain prior history.

For each checkpoint, all **512 trained-target FP32 truth probabilities match the
retained native window evaluation bit for bit**. Each complete PPM prior stream
also matches the original training capture. Thus the observed training gains
survive the deployed initialization, history, priors, resets and target alignment
on these positions. No internal value was substituted into inference.

## Matched measurements

N is negative log2 of the actual native FP32 truth probability before output
half-conversion and guarding. F is the sum of negative log2 probabilities from
the actual integer Q16 values entering the arithmetic coder, over the eight bits
corresponding to each target. These are different distributions; totals are added
only within their own measurement level.

| Checkpoint | Partition | Targets | Native N, bits | Final F, bits |
|---|---|---:|---:|---:|
| P | Trained | 512 | 1,100.611418 | 1,074.969696 |
| P | Other neural | 150,600 | 283,099.719644 | 265,954.678003 |
| P | No neural | 98 | N/A | 29.143444 |
| P | Total | 151,210 | 284,200.331062 | 267,058.791143 |
| A | Trained | 512 | 131.407373 | 308.925528 |
| A | Other neural | 150,600 | 479,891.872352 | 323,594.071832 |
| A | No neural | 98 | N/A | 30.803735 |
| A | Total | 151,210 | 480,023.279725 | 323,933.801094 |
| J | Trained | 512 | 128.726667 | 298.743593 |
| J | Other neural | 150,600 | 423,784.438325 | 317,039.176367 |
| J | No neural | 98 | N/A | 29.950869 |
| J | Total | 151,210 | 423,913.164992 | 317,367.870829 |

N totals cover 151,112 eligible targets; F totals cover all 151,210 targets.
For X=A,J, deltas are X minus P; negative means improvement.

| Partition | A delta N, bits | A delta F, bits | J delta N, bits | J delta F, bits |
|---|---:|---:|---:|---:|
| Trained | -969.204046 | -766.044168 | -971.884752 | -776.226103 |
| Other neural | +196,792.152708 | +57,639.393829 | +140,684.718681 | +51,084.498364 |
| No neural | N/A | +1.660291 | N/A | +0.807425 |
| Total | +195,822.948662 | +56,875.009952 | +139,712.833930 | +50,309.079686 |

Both checkpoints improve the trained positions at both measurement levels. On the
other 150,600 eligible positions, neural and final-coder losses overwhelm those
gains. Whole-population neural cost therefore worsens, as does final-coder cost.
This is not a case where a better whole-population neural predictor is established
and only its combination regresses.

## Archive reconciliation and observer controls

The observed archives are byte-identical to their retained, unobserved native
archives: P 33,429 bytes, A 40,538 bytes, J 39,717 bytes. For each checkpoint,
independent decoding reconstructs the exact raw fixture; encoding the restored
fixture repeats the archive. All four captured streams (final probabilities and
truths, neural truth probabilities, token/reset rows, PPM priors) also match across
encode, decode and repeat. Captured coded bytes independently reproduce the bound
token/reset geometry.

The measured residual is epsilon = 8*(B_X-B_P) - delta F(all):

| Checkpoint | Archive delta, bytes | Archive delta, bits | Delta F(all), bits | Epsilon, bits |
|---|---:|---:|---:|---:|
| A | +7,109 | +56,872 | +56,875.009952 | -3.009952 |
| J | +6,288 | +50,304 | +50,309.079686 | -5.079686 |

These residuals reconcile the measured finite archive differences with the logged
integer-probability costs. They include remaining finite coding/framing effects;
they are not a universal error bound. Delta F minus delta N is not a causal
mixer-loss decomposition and is deliberately not reported as one.

## Closure and next research constraint

The analysis-only candidate is `fx2_training_trajectory250k_q0_v1`, owner
`codex-training-attribution-20260920`, source/ownership publication `0371a2673`,
job `20260920T211447Z_85cfcf79b5`. The existing lab owns execution; maintained
adapters own native observation and cost analysis. Component authority and codec
semantics are preserved, with no new operational entrance.

All 19 explicit native-group tests pass, including five targeted checks for mask
alignment, disjoint cost reduction, reset timing, invalid coordinates and unique
native source anchors. The native timing fixture runs with UBSan. Python compile
and adapter import checks pass. Independent Python reduction checks every
partition within 1e-7 bits, verifies encode/decode/repeat capture identities and
rehashes all 285 gate artifacts.

The guarded build plus nine codec phases close without violations in 358.2879
seconds. Peak cgroup memory is 6,588,637,184 bytes and peak allocated scratch is
730,824,704 bytes; owned process/cgroup cleanup completes. CPU 2, 10 GB resident,
zero swap, 18 GB logical scratch and a 1,800-second elapsed stop were declared.
The 32 GiB virtual allowance accommodates the original sparse PPM mapping.
These are shared-host observer diagnostics, not release runtime qualification.

**The next unresolved issue is preserving useful predictions outside the
optimization windows.** The result supports investigating training coverage or
preservation of the parent's behavior. It does not select either remedy, justify
increasing this profile's update budget, or prove that the approximate Jacobian
caused the degradation. A specific mixer failure would require a controlled
intervention; these different distribution costs do not establish one. No new
training profile or larger population is authorized by this diagnostic closure.

Keep P as the scale comparator and preserve A/J. The existing
[bounded delivery progress](fx2_matched_training_20260920.md#complete-bounded-delivery)
remains: executable-form complete fixture totals are 7,642,117 bytes for P and
7,598,975 for J, a 43,142-byte saving. J's 1 MB archive-plus-two-model saving is
25,747 component bytes, not a full submission score. Observer files and repeated
research artifacts are not a new delivery package. Cross-history work remains
parked; the 96M target and 95M stretch are unchanged.
