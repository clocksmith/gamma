# CMIX-obias Scalar-MIDAS64 PPM0 q0 v2 Contract

## Claim boundary

The deployed source-built parent uses a compiled constant output-logit prior:

```text
bias_t[j] = 0.15f * logf(max(ppmd_t[j], 1e-6f))
```

This candidate tests whether the reliability of that PPMd prior varies within
the transformed stream and can be adapted causally with one decoder-visible
scalar per 64-byte segment. It does not claim that the parent is static: every
ordinary PPMd, LSTM, mixer, SSE, and optimizer update remains active.

## Exact population and timing

Segments are consecutive, nonoverlapping groups of 64 bytes in the transformed
stream entering CMIX. Segment byte indices are `0..63`.

- Bytes `0..31`: use the exact parent gate `g0 = 0.15f` and collect gradient
  and curvature after each eligible byte truth is decoded. Global transformed
  byte `0` is ineligible because the parent has not yet constructed an obias
  row; segment zero therefore has 31 observations (`1..31`).
- Boundary after byte `31`: construct one correction `delta`.
- Bytes `32..63`: use `g = g0 + delta` without further episodic updates.
- Boundary after byte `63`: discard all episodic state and restore `g0`.

The midpoint and reset are decoder-synchronized. The first adapted prediction
is byte `32`; no statistic from byte `32` or later affects its own probability.

## Exact parent call order

The parent constructs the prior for byte `t+1` in
`KhObiasPrior::Advance(y_t, ppmd_for_t_plus_1)` after byte `t` completes. The
candidate preserves that call and binds this order at every byte boundary:

```text
1. Preserve s_t and the already-used x_t before ordinary Lstm::Perceive reuse.
2. Execute the ordinary parent truth/update path at its unchanged call site.
3. If t is an eligible first-half byte, accumulate grad_t and var_t.
4. If segment_byte(t) == 31, construct/select the second-half gate.
5. If segment_byte(t) == 63, discard G/H/delta and restore g0.
6. Execute unchanged Advance(y_t, ppmd_for_t_plus_1), which materializes the
   bias row for byte t+1 using the gate selected in step 4 or 5.
```

Thus `Advance(byte31, p32)` uses the new D/K/S midpoint gate, and
`Advance(byte63, p64)` uses restored `g0`. Byte `0` has the parent's all-zero
initial bias and contributes no synthetic gradient, curvature, or denominator.

## Exact learning signal

For an eligible completed first-half byte `t`, define `x_t[j]` as the exact FP32 value
already used by the parent prior:

```text
x_t[j] = logf(max(ppmd_t[j], 1e-6f))
```

Define `s_t[j]` as the exact normalized 256-way Byte-LSTM output used for that
byte after adding the parent output bias and before the ordinary truth update.
The implementation must copy this row before `Lstm::Perceive` can overwrite or
reuse it. Raw byte `y_t` is mapped through the existing `byte_map_`; no new
vocabulary order is introduced.

The scalar loss derivative and exact softmax curvature are:

```text
mu_t   = sum(j=0..255) s_t[j] * x_t[j]
grad_t = mu_t - x_t[y_t]
var_t  = sum(j=0..255) s_t[j] * x_t[j] * x_t[j] - mu_t * mu_t
```

Accumulate sequentially in increasing raw-byte order:

```text
G = sum(eligible first-half t) grad_t
H = sum(eligible first-half t) max(var_t, 0.0f)
```

At the midpoint:

```text
denom = max(H, 0x1p-12f)
delta = clamp(-G / denom, -0.125f, +0.125f)
g     = 0.15f + delta
```

This is a one-dimensional clipped Newton step on the exact biased Byte-LSTM
softmax surrogate. It is not presented as the derivative of downstream SSE or
the final arithmetic probability.

## Frozen arms

```text
P  untouched parent with constant gate 0.15f
K  collect G/H and construct delta, but apply an exact zero correction
G  persistent global online Newton control, separately specified before use
D  target: first-half statistics adapt the second-half gate, then reset
S  shifted control: apply the preceding segment's delta to the current segment
```

`G` is held until its persistent update/reset law is separately frozen. Opening
execution is `P/K/D/S`; no missing `G` result may be represented as a pass.

For `S`, segment zero uses `delta=0`; at every later segment, the delta produced
from the immediately preceding segment's first half is applied to bytes
`32..63` of the current segment. This is causal but intentionally misaligned.

## Parent and arithmetic invariants

- Ordinary persistent Byte-LSTM, CMIX mixer, SSE, PPMd, Bit-LSTM, optimizer,
  memory, and coder updates execute at their exact parent call sites/cadence.
- The candidate changes only the scalar multiplying the already existing PPMd
  output-logit row during the second half of each segment.
- `P` must be byte-identical to the clean parent. `K` must execute live G/H,
  midpoint, clip, and reset arithmetic yet remain probability-, state-,
  payload-, and archive-identical to `P`.
- Encoder, repeat encoder, and bare decoder must match segment index, G, H,
  delta, gate, byte-LSTM output state, all parent state, and coder state.
- The PPM0 disk-residency correction is infrastructure only and must first pass
  its independent clean/treatment byte-identity joint decision.

Reference arithmetic is scalar IEEE-754 FP32 under `FE_TONEAREST`, precise
floating-point compilation, FMA contraction disabled, fast-math disabled,
FTZ/DAZ disabled, fixed reduction order, and one thread. It reuses the parent's
`logf` values rather than recomputing them in another translation unit.

## Opening decision and accounting

Run `P/K/D/S` serially on the frozen opening 250,000-byte population from clean
disk-backed scratch. Every arm requires a finite terminal archive, exact bare
inverse, deterministic repeat, complete probability/state receipts, process
and process-tree RSS at most 9,765,625 KiB, allocated scratch at most
100,000,000,000 bytes, complete cleanup, and complete package accounting.

Opening promotion requires:

```text
P payload == clean parent payload byte-for-byte
P payload == K payload byte-for-byte
K shadow update count > 0
all encode/repeat/decode scalar state receipts identical within each arm
D payload bytes < P payload bytes
D payload bytes < S payload bytes
incremental required package bytes <= 65,536
```

Opening evidence is diagnostic. Promotion remains `250KB -> 1MB -> opening
10MB -> two distant 10MB slices -> 100MB -> 1GB`, with the established 10MB
gross gate of at least 40,793 payload bytes and 100MB gate of at least 407,925
bytes. Separate gains cannot be added without a synchronized joint replay.
