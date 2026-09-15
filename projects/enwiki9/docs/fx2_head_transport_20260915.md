# Optional learned-head correction with an unchanged parent

The previous native head experiment improved the neural component's printed
loss by about 97.2 ideal bytes while making the final archive 175 bytes larger.
That is a measured reason to test integration, not evidence of future savings.
This candidate retains exactly that learner, including its learning rate,
projection radius, features, label alignment and original article resets.

The original transformer probabilities always go to the original CMIX models.
All their updates remain authoritative. The learned distribution is used only
to form an optional correction at the arithmetic coder. Encoder and decoder
rebuild it from decoded truths; they receive no learned trace or adapter file.

Let p be the final parent count, b the original neural bit count, a the learned
neural bit count, and Q=65536. All counts are strictly between zero and Q.
Compute the corrected count with exact integer intermediates:

    n = p * a * (Q-b)
    d = n + (Q-p) * (Q-a) * b
    t = clamp(round(Q*n/d), 1, Q-1)

Rounding is nearest with upward ties. When a=b, return p exactly. In real
probability arithmetic, this adds the learned neural log-odds difference to
the final parent log-odds; when p=b it recovers a. Neither identity proves gain.
The learned and original distributions use the native FP16 roundtrip, floor,
vocabulary mapping and float summation. At every bit the reproduced original
neural count must equal the native ByteModel count, or execution fails.

Eight bit-position contexts mix p and t with two positive integer weights
summing to 2^32, initially equal. Update each context on decoded truth using
Bayesian likelihood weights, minimum one, and largest remainders with low-index
ties. Weights persist across articles; the unchanged head resets normally.
Forced native overrides bypass the correction and posterior update.

In ideal unrounded arithmetic, the Bayesian mixture loses at most eight prior
bits to the parent. For W=2^32, the implemented posterior update assigns each
component at least (1-2/W) times its exact posterior probability. Thus its
unrounded probability mixture has regret at most

    8 + N * log2(W/(W-2)) bits

against the always-parent path over N active events. This bound excludes Q16
probability rounding, finite-coder overhead and program cost. It therefore
cannot certify a smaller archive, eligibility or a winning result.

P emits the parent with learning disabled. K learns the same aligned head and
posterior as D while coding with the parent. D codes with the optional mixture.
S learns from cyclically wrong labels with the same capacity and update timing.
All original parent float probabilities and decoded truths must match across
arms. K/D complete introduced states must match. K's head state must also match
the retained head experiment byte for byte, proving the learner was preserved.

The gate freezes one exposed opening-250KB configuration, 16 phases and the
same native resource ceilings. Complete head snapshots cover 74 boundaries;
transport snapshots cover 591 boundaries, including all weights, CDF arrays,
prefix coordinates and clocks. Frozen feature/logit SHA blocks, independent
inverses/repeats, original P/K archive parity and untraced D identity are required.

Synthetic checks pass 65,535 identity counts, 100,000 independent odds
comparisons and 8,000 comparisons to the native ByteModel prefix operation.
These are implementation tests, not corpus savings. The original head learner
and both controls have already undergone their separate native experiment.

A nonpositive P-D or S-D closes this fixed integration as a scientific negative.
A resource or correctness failure invalidates the affected comparison. No
further rate, feature, rank or reset rescue is included in this development
budget. A positive result still needs priced delivery and confirmation. The
90,000,000-byte target has no verified full-corpus witness.

[Contract](../operations/adaptive/experiments/fx2_head_transport_opening250k_v1.json)
[Plan](../operations/provenance/fx2_head_transport_opening250k_v1_plan.json)
[Core](../lib/fx2_head_transport_v1.hpp)

## Startup correction

Version 1 aborts before its first coded bit. The original global
`byte_mixer_output` starts at zero, triggering a forced prediction; the initial
ByteModel distribution is uniform. The synthetic comparison had tested the
ByteModel operation without that caller initialization. A separate first-call
reproducer confirms the original wrapper abort. No complete archive exists.

Version 2 permits only position zero with an inactive correction and both native
and parent count one. Every subsequent bit retains the strict native-count
comparison. The learner, odds calculation, posterior, population and controls
are unchanged. All four arms pass the corrected startup plus seven following
native bit updates, alongside the full previous unit comparison. This is an
implementation repair, not a parameter or hypothesis rescue.

The v2 unit receipt also corrects an invocation spelling in earlier descriptive
unit metadata: use `taskset -c 3`, not `taskset -c3`. The first erroneous v2
invocation and successful successor logs are retained separately.

[Failed execution](../operations/provenance/fx2_head_transport_failure_20260915.json)
[Corrected contract](../operations/adaptive/experiments/fx2_head_transport_opening250k_v2.json)
[Corrected core](../lib/fx2_head_transport_v2.hpp)

## Closed native comparison

[Terminal](../operations/provenance/fx2_head_transport_terminal_20260915.json)
and [validated reflection](../operations/adaptive/reflections/20260915T025312Z_f55e6caa2e.json)
close all 16 phases. P/K are 33,429 bytes; D/S are 33,430. Thus P-D=-1 and
S-D=0. Independent inverses, repeat archives, untraced D, clean build repeats,
all original pre-coder probabilities/truths, 74 learned-head state boundaries,
591 optional-mixture state boundaries and frozen feature/logit hashes pass.
The learner matches the prior experiment at every recorded state boundary.
All discovery resource guards and cleanup pass. The configuration is retired.

Equal D/S archive sizes do not imply equal predictions or equal archive bytes.
Complete original model parameters, optimizer state and update counters were
not separately serialized. The original pre-coder probability stream and
frozen-feature digests are the protected observations actually measured.
The newly introduced states have their own complete recorded witnesses.

The separate production release's 40,994 component-byte improvement is not
inherited here. This experiment adds 62,957 overlapping source/binary/option
component bytes and loses one archive byte. Its diagnostic net is -62,958;
complete official package accounting remains unresolved.

A read-only comparison of the closed traces finds 42,413 changed Q16 events:
24,360 improve the truth probability and 18,053 worsen it. Summed ideal saving
is approximately -8.020055 bits, consistent with the one-byte archive loss.
For any convex mixture of these two fixed final P/D streams, even selecting
the better truth probability with future knowledge gives at most 404 ideal
bits (50.5 bytes). That ceiling uses exact integer products and shifts.
It does not cover the underlying unmixed expert, other learned states or
populations, finite archive bytes, or arbitrary changes to the algorithm.
See the [trace analysis](../results/fx2_head_transport_opening250k_v2/closure/trace_pair_analysis.json).

Preserving the protected observations did not produce a paying correction.
The comparison does not isolate the cause of the earlier 175-byte regression:
optional mixing and integration placement changed together. No rate, feature,
rank, calibration or reset rescue follows in this development sequence.
Independent confirmation is not authorized for this rejected configuration.

[Verified unit-command corrections](../operations/provenance/fx2_unit_command_errata_20260915.json)
preserve the earlier receipts and provide successfully rerun, explicit compiler
and execution argument lists for their unchanged test sources.
