# Hidden-signature cache: one prospective conditional comparison

The static dense and sparse residual families failed their declared ideal-cost
bounds. The subsequent fixed causal linear family was also checked through its
actual finite coder: none of its six amplitudes improved the parent payload.
Those results remain closed. This experiment tests a different information
source: earlier next-byte labels associated with similar pre-truth hidden states.

Continuous hidden-state caches are established prior art, including Grave,
Joulin and Usunier, *Improving Neural Language Models with a Continuous Cache*,
arXiv:1612.04426v1, <https://arxiv.org/abs/1612.04426>. No external implementation
is copied. This independently written bounded integer cache is a proposed Gamma
mutation, not a claim of inventing nearest-neighbor language modeling or winning
Hutter. Its archive improvement is unknown before this run.

## Frozen realization

Use the authenticated native parent observations on exposed opening raw
`[0,250000)`: 151,210 WRT bytes and 1,209,680 MSB-first bit decisions. The
32 ternary signs come from the established ordered groups of six final normalized
hidden coordinates. The 98 invalid startup/reset-byte features remain zero.
No feature extraction, parent learning, corpus selection, or calibration sweep
is introduced.

Retain 4,096 valid, nonzero 64-bit packed signatures and their observed next byte
in FIFO order. Before each byte, select up to 32 entries of ternary Hamming
distance at most eight, nearest first and newest first within a tie. Each label
receives weight `9-distance`. The cache persists across native reset pieces.
Invalid/zero signatures do not query or insert. Insert only after all eight bits
of the byte have been decoded. Current truth is unavailable during its query.

At bit position `r`, restrict the histogram to the already decoded byte prefix.
If its total is nonzero, form cache count `h=round_half_up(65536*ones/total)`
and specialist count `e=floor((3*c+h+2)/4)`, where `c` is the exact parent count.
Otherwise `e=c`. Endpoints remain strictly between zero and 65,536.

For each of eight bit positions, initialize parent/specialist integer weights to
`2^31,2^31`. Emit their weighted mean count, rounded half up. Following the truth,
multiply each weight by its truth count, then normalize to sum `2^32` with a
minimum weight of one. Allocate the remaining `2^32-2` mass by largest remainder;
ties favor the parent. Skip this update when `e=c`. Products use unsigned
128-bit integers. There are no fitted coefficients or external model downloads.

## Arms, exactness, and pricing

- P is the authenticated native trimmed-parent archive, 33,429 bytes.
- K executes the complete cache/controller but emits the parent count.
- D emits the cache mixture, keeping the original parent predictions/learning.
- S has the same geometry and arithmetic but pairs each signature with the
  previous decoded byte. The first pair uses its own label. This changes the
  association, rather than permuting labels and allowing a fit to undo it.

K and D must have identical complete controller state at the declared boundaries;
P and K must have identical counts and archives. Each K/D/S archive is encoded,
independently decoded, and repeated in separate processes. Repeat starts from
the decoded modeled bytes. It is not a new native preprocessing pass. All raw
inverses must match the canonical 250,000-byte fixture. The state serializer
includes every mutable cache/controller field, excluding the constant arm label.
Hash it initially, every 2,048 decisions, and at the end. Hash all probability
counts and arithmetic intervals; compare intervals during independent decoding.

The first stage rechecks native encode/decode/repeat observations and arithmetic
replay. It exports truth-free `parent.q16` (2,419,360 bytes), `signatures.bin`
(1,360,890 bytes, one packed signature plus validity byte per modeled byte),
and the original 46-byte archive prefix. Conditional decoding also needs the
411,996-byte dictionary. These are supplied dependencies, not free decoder
knowledge. A pass only justifies separately priced native integration; it is
not a standalone codec, confirmation, larger-scope authorization, or prize score.

Count actual conditional archives. The constant algorithm needs no additional
archive header, but its source and binary costs remain payable. Report authored
header/bridge bytes and the built shared-library bytes separately; these are
alternative component measurements, not a complete package or additive charge.
The authored kernel ceiling is 16,384 bytes; experimental library ceiling 65,536.
Require D smaller than P and S, all exactness checks, repeat builds, and resource
compliance. If it loses, retire this configuration without a radius, capacity,
mixing-strength, or label-shift rescue. Missing evidence or resource stops are
execution outcomes, not measured compression losses.

## Execution and checks

Twelve guarded phases: two independent library builds; exact parent projection;
K encode/decode/repeat; D encode/decode/repeat; S encode/decode/repeat. Use CPU 3,
1 GiB memory, zero swap, 128 MiB scratch, and a 900-second execution stop. Timing
is diagnostic. Source, ownership, inputs, toolchain, and contract are published
before fresh resource admission and canonical queue execution.

Seven synthetic tests compare the C++ kernel to a separate brute-force Python
implementation, check FIFO/tie semantics, insertion causality, malformed calls,
K/D state identity, independent arithmetic decoding, and separate CLI processes.
The first corruption test accidentally rewrote an identical byte; its failed
log is retained and the corrected test flips a bit. No synthetic gain is corpus
credit. Complete full-corpus score remains unknown; target is 90,000,000 bytes.
