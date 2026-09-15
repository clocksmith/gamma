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
