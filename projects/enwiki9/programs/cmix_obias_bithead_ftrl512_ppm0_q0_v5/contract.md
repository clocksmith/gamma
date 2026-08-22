# Bit-Head FTRL512 PPM0 v5 Contract

## Claim boundary

`cmix_obias_bithead_ftrl512_ppm0_q0_v5` is a prepared, uncompiled,
unexecuted Gamma-authored correction successor to sealed FTRL v4.
It has no measured compression gain, score credit, or prize status. It does not
mutate v1, v2, or v3. The external `cmix-obias` substrate remains fully
attributed and receives zero Gamma authorship or score credit.

The candidate retains the v3 probability-neutral PPM policy:

```text
CMIX_PPMD_RSS_BUDGET_MB=0ULL
```

That policy must independently prove payload identity and strict process-tree
RSS compliance before any compression result from this child can promote.

## Correction relative to v4

The D/O/R/S treatment and control probability trajectories are unchanged from
v4. v5 corrects K so that it executes D's gradient, diagonal curvature, tied
Walsh reconstruction, scalar-logit refresh, clipping, and receipt hashing while
injecting neither the reconstructed gate correction nor the logit correction.
This makes P=K a matched bookkeeping test rather than a partial-sidecar test.

The underlying hypothesis remains strictly causal follow-the-regularized-leader
adaptation: the adapter used for bit `t` depends only on coder probabilities,
head states, and truths from earlier bits in the same 512-coded-bit segment. A
diagonal local Gauss-Newton accumulator determines scale. There is no tuned
learning rate, PRNG, Gaussian generation, or coefficient blob. The candidate can
still fail because the local tangent omits future recurrent effects and local
statistics may not transfer even to the next coded bit.

## Coordinate and ordering

The coordinate is the post-preprocessing coded-bit stream. For `u=t mod 512`:

1. If `u=0`, clear only the episodic FTRL state before predicting the bit.
2. Construct the arm's adapter from events strictly earlier than `t`.
3. Run the ordinary bit-head recurrence and final probability path.
4. Supply exact integer probability `q_t` in `[1,65535]` to the range coder.
5. After truth `y_t` is decoded, update the episodic gradient and curvature.
6. After `u=511`, retain no episodic state into the next segment.

The native bit-head hidden/cell reset every 64 coded bits and every ordinary
CMIX update call site remain unchanged. Override bits contribute no gradient;
their normal head-state transition remains part of the synchronized trajectory.

## Local tangent

For each of the 32 bit-head cells, capture the adapted forward values `i_r`,
`g_r`, `o_r`, `tanh(c_r)`, and output weight `wout_r`. The terminal-logit
Jacobians, without the residual factor, are:

```text
dc_r  = wout_r * o_r * (1 - tanh(c_r)^2)
J_i,r = dc_r * g_r * i_r * (1 - i_r)
J_g,r = dc_r * i_r * (1 - g_r^2)
```

Coordinates 0..31 are `J_i`; coordinates 32..63 are `J_g`. Clamp every
coordinate to `[-8,8]`, multiply by `2^20`, and convert by C++ truncation toward
zero. This is explicitly a local straight-through tangent, not an exact
derivative of discrete code length or full recurrent BPTT.

## Rank-8 deterministic basis

Define:

```text
H(row,c) = (-1)^popcount(row & c)
B[j,c]   = H(j+1,c) / 8,  j=0..7, c=0..63
```

For each event and rank coordinate, using signed integer division toward zero:

```text
Jj_q20       = clip(sum_c H(j+1,c) * Jc_q20 / 8, -8*2^20, 8*2^20)
residual_num = q_t - y_t*65536
g_j         += residual_num * Jj_q20 / 65536
pvar_q20     = q_t * (65536-q_t) / 4096
Jj2_q20      = Jj_q20 * Jj_q20 / 2^20
h_j         += pvar_q20 * Jj2_q20 / 2^20
```

All products and accumulators use checked signed 64-bit arithmetic. The scalar
terminal-logit coordinate uses `J_q20=2^20` and the same equations.

Before the next prediction, with fixed regularizer `lambda_q20=2^20`:

```text
theta_j_q20 = clip(-g_j * 2^20 / (h_j + lambda_q20), -2^18, 2^18)
delta_c_q20 = clip(sum_j H(j+1,c) * theta_j_q20 / 8, -2^18, 2^18)
```

The logit correction is the identically normalized scalar `theta_l_q20`.
Corrections are exactly dyadic FP32 values and are injected into input/candidate
preactivations before sigmoid/tanh and into the terminal logit before sigmoid,
clipping, and integer probability quantization. Forget/output gates and every
other model remain unchanged.

## Matched arms

```text
C  clean external source with PPM0 only
P  instrumented parent, no collection or injection
K  complete D gradient, curvature, reconstruction, logit, and receipt
   bookkeeping, with zero gate or logit injection
O  online FTRL terminal-logit correction only
R  D analysis rows 1..8, orthogonal reconstruction rows 9..16, plus logit
D  tied rows 1..8 analysis/reconstruction, plus logit
S  D update with prior-bit residual paired to the current Jacobian, plus logit
```

For S, the first residual in each segment is zero and the previous residual is
updated only after the current event. This is decoder-visible and causal but
deliberately breaks residual/Jacobian alignment.

## Determinism and qualification

The bound diagnostic is one thread with exact source, compiler, linker, flags,
environment, binary, overlay, head-blob, and corpus hashes. Integer traversal
order is rank-major then coordinate-major. FP32 Jacobian evaluation preserves
the parent's bound AVX2/FMA semantics for the host-specific diagnostic. A
portable scalar successor must freeze rounding, contraction, FTZ/DAZ, and prove
integer-probability, state, payload, and archive identity.

Opening qualification requires actual arithmetic archives, exact bare decode,
repeat byte identity, C=P payload identity, P=K probability/state/payload
identity, synchronized encode/decode receipts, live controls, finite arithmetic,
strict 9,765,625 KiB process-tree RSS, cleanup receipts, and incremental required
program material no greater than 65,536 bytes.

Promotion remains:

```text
250KB diagnostic
1MB calibration
opening 10MB hard gate: at least 40,793 bytes gross payload gain;
  package debt tracked separately
two disjoint distant 10MB transfer gates
100MB hard gate: at least 407,925 bytes net gain
1GB only after explicit authorization
```

No savings from v3, v4, NNCP, preprocessing, or another probability trajectory
may be added arithmetically. Any combination requires a new joint replay.
