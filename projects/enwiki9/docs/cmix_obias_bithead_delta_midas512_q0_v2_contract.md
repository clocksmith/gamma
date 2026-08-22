# cmix-obias Bit-Head DELTA-MIDAS 512 q0 v2

## Claim boundary

This is an unexecuted Gamma-authored causal-adaptation child of the externally
authored GPL-3.0 `cmix-obias` substrate. It has no measured compression gain,
objective credit, or prize status. The complete counted target remains at most
105,000,000 bytes, including archive and every required program/model asset.

The frozen `cmix_obias_deep_delta_midas64_q0_v1` experiment is not mutated. Its
operational status is `superseded_before_execution`, scientific verdict is
`none`, and score credit is zero. Its seeded independent gate maps remain a
historical random-direction control, not the target-bearing treatment.

## Source correction

`cmix-obias` has two recurrent systems. The 256-cell byte LSTM uses a coupled
input-forget update and exposes its gate errors only in deferred 64-byte BPTT.
The v1 `U_i/U_z` contract therefore did not match that implementation and could
not causally adapt its second half. v2 targets the separate frozen 32-cell
terminal bit LSTM, which has explicit PyTorch-order `i/f/g/o` gates and acts
directly on the final coder probability.

## Exact causal coordinate

The coordinate is the post-preprocessing CMIX coded-bit stream. For coded-bit
index `t`, segment phase is `u = t mod 512`.

- `u=0..255`: the parent prediction is unchanged; local eligibility is
  collected only after the coded truth is known.
- after `u=255`: the rank-8 state is finalized.
- `u=256..511`: the selected arm injects its frozen episodic correction.
- after `u=511`: current episodic accumulators are discarded.

Native head state reset every 64 coded bits remains unchanged. Because 256 and
512 are divisible by 64, both midpoint and segment start coincide with native
fresh recurrent state. All CMIX context, mixer, PPMd, byte-LSTM, optimizer,
feature-window, coder, preprocessing, and package behavior remains unchanged.

## Exact residual and local eligibility

Let `q_t` be the integer in `[1,65535]` returned by the terminal head and used
for the arithmetic range split, whose denominator is 65,536. Let `y_t` be the
already-coded truth. The straight-through terminal-logit derivative is:

```text
d_t = q_t / 65536 - y_t
```

This is explicitly a local straight-through tangent; it is not described as an
exact derivative of discrete code length. Override bits contribute zero
eligibility because the terminal head is bypassed for those bits.

For cell `r`, using the current head output weight `wout[r]`, input gate `i_r`,
candidate `g_r`, output gate `o_r`, and `tanh(c_r)` captured from the native
forward pass:

```text
dh_r  = d_t * wout[r]
dc_r  = dh_r * o_r * (1 - tanh(c_r)^2)
dai_r = dc_r * g_r * i_r * (1 - i_r)
dag_r = dc_r * i_r * (1 - g_r^2)
```

Future recurrent effects are deliberately excluded. Coordinates `0..31` are
`dai`; coordinates `32..63` are `dag`. No forget/output gate is injected.

## Deterministic projection and update

Each local gradient is clamped to `[-8,8]`, multiplied by `2^20`, and converted
to signed integer by C++ truncation toward zero. Accumulation is signed 64-bit
in coded-bit and coordinate order. No Gaussian, PRNG, coefficient blob, libm
projection, or platform-dependent traversal exists.

Define Walsh sign `H(row,c)=(-1)^popcount(row & c)`. For `j=0..7`:

```text
B[j,c] = H(j+1,c) / 8
m[j]   = clip(sum_t sum_c H(j+1,c) qgrad[t,c] / 2048,
              -2^18, 2^18)
```

All divisions are signed C++ integer division toward zero. `m` is Q20. The D
arm applies the tied projected gradient step with `eta=1`:

```text
delta_gate_q20[c] = -sum_j H(j+1,c) m[j] / 8
```

R reconstructs with rows `j+9`, an orthogonal Walsh subspace. S uses the prior
segment's `m` with D's tied transpose. O and D/R/S also apply the separately
accumulated terminal-logit mean with `eta_l=1`; O has no gate injection. Every
active gate or logit Q20 correction is clipped to `[-2^18,2^18]` before exact
dyadic conversion to FP32.

## Arms

```text
P=0  observationally instrumented parent; no eligibility or injection
K=1  complete eligibility bookkeeping; zero injection
O=2  current-segment terminal-logit update only
R=3  current-segment orthogonal-Walsh gate update plus logit update
D=4  current-segment tied-transpose gate update plus logit update
S=5  preceding-segment tied-transpose gate/logit update
```

P must reproduce the clean parent's payload. K must equal P in every returned
integer probability, sampled recurrent-state digest, payload, and inverse. D
must beat P, K, O, R, and S to support a deep causal-adaptation claim.

## Build and numerical contract

The diagnostic build is one thread, Clang 17/LLD 17, `-march=native`, head TU
`-O3 -ffp-model=precise`, parent AVX2/FMA semantics retained, and no PGO/LTO.
The upstream PGO profile is not reused for modified code. Adapter projection is
integer; FP operations occur only in the frozen local derivative and exact
dyadic Q20 injection. Compiler command, environment, binary hash, overlay hash,
upstream source hash, head blob hash, logs, RSS, scratch, and cleanup are receipt
fields. A later portable scalar successor must bind `FE_TONEAREST`, no FMA
contraction, FTZ/DAZ off, and prove identical integer probabilities and archive.

## Promotion ladder

The opening 250KB run is diagnostic only. It requires finite arithmetic, exact
repeat payload/archive, exact bare inverse, P payload identity, P/K probability
and state identity, live controls, and resource compliance. A positive D then
moves to 1MB calibration, opening and two distant 10MB gates, 100MB with at
least 407,925 bytes gross improvement under complete package accounting, and
only then isolated full-corpus qualification. No savings from a different
probability stream may be added without a fresh joint replay.
