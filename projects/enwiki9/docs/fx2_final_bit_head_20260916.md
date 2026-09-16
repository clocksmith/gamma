# Train the correction on coded-bit errors

The closed head-transport comparison improved no archive: P/K33429, D/S33430.
The released expert mixture now has three positive archive observations, but
its unchanged1MB confirmation saves51 bytes against1188 added source/option
bytes. Its hold remains in force. Neither result funds a larger gate.

This exploration uses deliberate lenses8 and9, seed `fx2_final_bit_head250k_v1`.
The selected premise is that an online learner should consume the actual final
coder residual rather than optimize a separate205-way neural loss. It is a new
binary-prefix model and training objective, not a rate/rank/reset rescue of the
frozen head, ternary32-feature table, block controller, or expert mixture.

Three alternatives were considered. Another mixture of the old fixed P/D streams
is deferred under its measured404-ideal-bit oracle ceiling. A deeper native MLP
gradient changes more state and lacks a bounded implementation; its unproven gain
is not borrowed. A structural donor extension is outside this family, but the
closed match-gap treatment failed against its parent and shifted control. The
selected final-bit learner has a defined loss, exact decoder procedure and an
executable kernel. There is no claim that these alternatives are impossible.

## Fixed realization

For each of255 binary byte prefixes, keep192 binary64 coefficients, initialized
to zero at an article reset. Use the existing normalized hidden vector h, with
phi=h/sqrt(1+sum(h_i*h_i)), captured before truth. No hidden-state hash substitutes
for values. Each coefficient row has Euclidean norm at most4. The correction is
u=w.phi. For the actual parent count c and Q=65536, compute

    q = c*exp(u) / (Q-c+c*exp(u))
    c' = clamp(floor(Q*q+0.5),1,Q-1).

Zero correction returns c exactly. The new head changes only the count supplied
to the coder. Original probabilities, predictor learning and neural state stay
authoritative. After truth y, update the selected row by

    w <- projection_to_radius4(w + 0.25*(y-c'/Q)*phi).

Projection uses fixed accumulation order and an interior radius3.999999999 when
needed. It changes no other row. Missing features produce the parent and no
update. Both aligned and control learning require an earlier byte in the current
article, so they have the same update opportunities. The prior byte and prefix
are derived solely from decoded truths. No pretrained or transmitted coefficients
are supplied. Online state costs memory and compute; implementation and options
remain paid. Existing model and dictionary remain required components.

P runs unchanged parent probabilities. K computes and trains the aligned head
but emits parent counts. D emits its corrected counts. S trains on the same bit
position of the immediately preceding decoded byte, while following the actual
current prefix. It has identical dimensions, update count and arithmetic. This
control destroys current-label alignment without a learnable feature renaming;
it can retain real lag correlation. It is not claimed to remove all information.

## Mathematical boundary

With a fixed parent probability p and causal feature phi, smooth ideal gain is

    F(w) = y*u - ln(1-p+p*exp(u)), u=w.phi.
    gradient F = (y-q)*phi.
    Hessian F = -q*(1-q)*phi*phi^T, negative semidefinite.

Thus the per-event objective, and a sum evaluated at one fixed row, is concave.
The actual update uses the rounded count. Rounding and clamping differ from q
by less than1/Q, so the gradient perturbation has norm below1/Q because norm(phi)
is below1. This is a bounded approximation, not the derivative of a discrete
archive length. Changing coefficients online does not establish a static optimum,
an archive improvement, a global best algorithm or the90M target.

Before each bit, both sides have equal parent state, prefix, head weights and
features. They calculate equal counts; decoded truth then produces equal head
updates and unchanged parent updates. Induction supplies the synchronization
argument. Native inversion/repeats must still check the implementation. The
binary64 exp/sqrt implementation is pinned for discovery; cross-build and
cross-host arithmetic qualification remains outstanding.

## Bounded discriminator

One exposed opening250KB population, raw[0,250000),151210 modeled bytes. One
realization, no rate/radius/row-count/feature/reset sweep. Compare P/K/D/S with
independent inverse, restored-raw repeat, P/K archive identity, full introduced
state witnesses, protected parent probabilities/truths and hidden/logit digests.
Require untraced D to equal traced D. Rebuild source independently before use.
Full original optimizer/parameter state is not serialized and is not claimed.

Report actual archive gain against P and S, separately priced source ZIP/option
and executable increments, native resources and unresolved package closure. A
valid nonpositive P-D or S-D retires this fixed candidate. A positive archive
result that does not pay the measured component remains held. Only a paying
result can authorize considering a frozen confirmation; it does not authorize
full1G. Correctness/resource failure is incomplete, not a compression verdict.
No gain, source reduction or full-corpus forecast is inherited from another child.

The current deliverable is a tested kernel and native gate under preparation.
Synthetic state agreement is not an arithmetic decode or corpus result. Target
90000000 complete bytes; verified full1G score unknown; objective credit0.

Prior evidence:
[head transport](../operations/provenance/fx2_head_transport_terminal_20260915.json),
[mixture confirmation](../operations/provenance/fx2_expert_confirm_terminal_20260916.json),
[match gap](../operations/provenance/fx2_match_gap_terminal_20260916.json).
