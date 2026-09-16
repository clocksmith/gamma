# Attention-value error feedback: kernel boundary

This is a proposed mutation of the paid native transformer, not an integrated
codec or a compression result. The current 10MB trimming comparison is unchanged.

The bound source computes FP32 attention values `vf`, normalizes by each head's
scale, clips to `[-128,127]`, and rounds to int8 before caching. The existing
KVF32 option only expands those int8 values. It restores no discarded precision.
Instead, this candidate retains the rounding remainder in bounded causal state.

The principle is established error-feedback/sigma-delta quantization:
[Ohno et al.](https://arxiv.org/abs/1609.01383) analyze feedback quantizers, and
[O'Connor and Welling](https://arxiv.org/abs/1611.02024) apply sigma-delta ideas to
neural activations. These papers supply neither enwik9 evidence nor novelty for
this principle. The implementation and proposed native mutation are authored
here; no external code, model or package is installed.

## Exact kernel

Set `Q=65536`. Let `z_t` be the parent's clipped, normalized FP32 value, and
`n_t=round_even(Q*z_t)`. Per value coordinate, initialize `r_0=0`, then compute

```
a_t = n_t + r_(t-1)
q_t = clamp(round_even(a_t/Q), -128, 127)
r_t = a_t - Q*q_t
```

All state updates are integer operations. Q16 conversion is explicit and rejects
nonfinite inputs. It differs from the original quantizer through both feedback
and at most half a Q16 unit of initial rounding. The prototype does not claim
zero-feedback native parity; the proposed K arm must use the original quantizer.

For every finite sequence of valid integer inputs and initial
`|r_0| <= Q/2`, induction gives `|r_t| <= Q/2`, including saturated endpoints.
The sum `a_t` lies in `[-128.5Q,127.5Q]`; nearest-even rounding leaves at most a
half-unit remainder. Clamping at either endpoint preserves that bound. Every
intermediate fits int32. Residual `+32768` is valid, so int16 is insufficient.

The exact conservation identity is

```
q_t - n_t/Q = (r_(t-1) - r_t)/Q.
```

For any fixed interval `[l,r]` and fixed real weights `w_t`, summation by parts
therefore yields

```
sum w_t*(q_t-n_t/Q)
  = (w_l*r_(l-1) - w_r*r_r
     + sum_{t=l}^{r-1} (w_(t+1)-w_t)*r_t) / Q.
```

Its absolute value is bounded by

```
(|w_l| + |w_r| + sum |w_(t+1)-w_t|) / 2.
```

The first term disappears when the interval begins with zero residual. For a
uniform mean over N positions, this gives `1/N`, or `1/(2N)` from reset. Q16
input rounding adds at most `sum |w_t|/(2Q)` relative to `z_t`. Multiply these
bounds by the head's positive value scale to recover value units.

These are local exact-arithmetic bounds for fixed values and weights. They do
not bound the native floating-point attention implementation, clipping error
relative to unclipped values, changed Q/K trajectories, neural loss, archive
size, or full-corpus performance. They also do not imply that attention weights
vary slowly in temporal order; that premise must be tested.

A counterexample is already in the tests: two inputs of `32113/Q` produce
feedback outputs `[0,1]` instead of the parent's `[0,0]`. The uniform mean is
closer to the inputs, but weights `[0,1]` produce a larger error. Better mean
preservation is not universally better prediction.

## Implementation evidence and next discriminator

The C++ kernel and independent rational Python reference pass nine tests:
20,077 general integer vectors; all 131,074 endpoint/residual combinations;
20,018 FP32 conversions; four invalid states; one reset probe; 2,080 uniform
subranges; 100 arbitrary weighted trajectories; causality, malformed-certificate
rejection, and the explicit unfavorable-attention example.

The first test run incorrectly expected the endpoint `127` with residual
`-1/2` to retain output `127`. Nearest-even correctly yields `126` and residual
`+1/2`. The failed test, source snapshot and corrected passing run are retained.
No kernel, rounding rule, range or hypothesis was changed to repair that test.

The source profile has three attention layers with 192 values each. A future
native integration needs 576 int32 residuals, or 2,304 runtime bytes; this is not
transmitted model data. Source and executable additions still have to be priced.
It must update after decoded inputs, reset with the model, and preserve the
existing int8 cache layout, paid weights, Q/K quantization, and parent learning.

Proposed controls are unchanged P; K computing discarded feedback bookkeeping
while using the original quantizer; D using aligned per-coordinate feedback;
and S borrowing the previous residual from the next coordinate within each
64-value head. There is no refit that could undo S's misalignment. A synthetic
example distinguishes D and S, but actual corpus control separation is unproved.

The next task is one native 250KB P/K/D/S mutation with exact inverse, repeat,
P/K probability/archive parity, bounded residual-state observations, and actual
archive/package comparison. Do not promote from this local theorem. Do not
sweep feedback strengths, layer subsets or residual widths after results. The
90,000,000-byte witness remains absent.
