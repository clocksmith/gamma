# NNCP v3.3 LibNC CPU encode-only closed-block Q1

Candidate:
`nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1`

## Claim boundary

This is a zero-credit teacher headroom gate. NNCP `--encode_only` is not a
decoder and cannot become a Hutter score, forecast input, package claim, or
full-corpus proof. Q1 asks whether its exact full-dictionary information source
has target-scale arithmetic headroom on one mature, causally closed native
block when executed continuously from symbol zero.

```text
target                         108,000,000 bytes
verified full-1G result        unknown
best counted forecast          109,389,323 bytes
remaining forecast debt          1,389,323 bytes
new score credit                         0 bytes
```

Q0 supplied a sampled future-symbol perturbation invariant and exact small-run
archive neutrality. It did not universally prove causality and it did not
measure a mature population.

## Why the previous Q1 is invalid

NNCP rounds the nominal 500,000-symbol enwik9 block to a multiple of
`64 * 32`:

```text
native block size              499,712 symbols
full-run boundaries            0, 499712, 999424, 1499136, 1998848, 2498560
```

Stopping at symbol `2,229,154` changes the final block's stream layout and
model trajectory. Running through `2,498,560` but charging only original
ordinals `[2,000,597, 2,229,154)` is also invalid: the 32 streams are evaluated
in time-major order, so charged predictions can use already executed truth
from other streams that maps beyond raw byte `9,999,992`. That is an uncharged
future-population condition.

The v1 attempt is quarantined with no scientific verdict. This plan changes the
population and therefore uses a new candidate ID.

## Frozen causally closed population

Use the complete preceding native block:

```text
continuous execution symbols  [0, 1,998,848)
charged NNCP symbols           [1,499,136, 1,998,848)
charged symbols                499,712
raw interval                   [6,757,802, 8,991,577)
raw bytes                      2,233,775
WRT byte interval              [4,182,331, 5,618,556)
joint P1 rows                  [33,458,648, 44,948,448)
```

Both raw endpoints are exact NNCP symbol-map boundaries and exact WRT
emission-group boundaries. The complete native block is charged in NNCP
execution order. No trace row may be reordered by original ordinal.

The source package, full dictionary, preprocessed stream, symbol map, exact
JANUS-plus-quotient P1 trajectory, WRT store, official inverse dictionary, and
raw input are receipt-bound. The local raw 10M file must equal the first
10,000,000 bytes of the receipt-bound 1G corpus, and both full file hashes must
match their receipts.

The full dictionary is free teacher/preprocessor information in Q1. A pass
would not isolate neural-model gain. Any constructive successor must transmit,
replace, or explicitly account for it.

## Probability contract

The native observer records a 15-bit integer probability for zero:

```text
prob0 = P(bit=0) * 32768
```

The exact project range coder accepts a 16-bit probability for one. Convert in
a wider integer domain before serialization:

```text
p1 = 2 * (32768 - prob0)
```

Every consumed `prob0` must be in `[1, 32767]`; every converted `p1` must be an
even integer in `[2, 65534]`. Probability and truth lengths must be asserted
equal before coding so `zip` cannot silently truncate.

## Frozen execution and integrity contract

Build the indexed observer from the immutable source tarball. Clear all
inherited observer and preload variables. Before the complete-block execution,
run the receipt-bound original binary, patched binary with observation off,
and patched binary with observation on for exactly 10,000 full-dictionary
symbols. All three archives must be byte-identical. The observed smoke trace
must cover every original ordinal once, use vocabulary `16,392` on every row,
match the frozen preprocessed truth, survive the exact probability conversion,
and decode its finite arithmetic stream exactly.

The full execution must satisfy:

```text
source, dictionary, input, map identities       exact
verified original libnc.so is runtime libnc.so  exact
local 10M equals receipt-bound 1G prefix         exact
continuous execution through symbol 1998848     required
complete native block trajectory                required
original ordinal permutation                    exact
charged original ordinals [1499136,1998848)     exact
charged events preserved in execution order     exact
trace vocabulary                                exactly 16392
native branch paths and truth                    exact
prob0 and converted p1 domains                   exact
process-tree peak RSS                            <= 9,765,625 KiB
joint and teacher arithmetic decode              exact
WRT/raw population boundaries                    exact
Git commit, RSS guard, and tool dependencies      hash-bound
```

Any preexisting non-quarantine artifact in the candidate result namespace makes
startup fail before the first write. A failed execution must be moved intact to
a named `quarantine_*` directory before any retry. Full-run, smoke, build,
parent, trace, guard, and decision artifacts are never overwritten or reused. A
guard receipt is valid only when both its status is `complete` and its recorded
return code is zero. The receipt-verified original `libnc.so` must be the exact
file selected from the original binary's runtime library directory.

## Decision

Let `A_J` be the independently terminated JANUS-plus-quotient stream over the
frozen WRT interval, and `A_N` the independently terminated converted NNCP
branch stream for the complete native block:

```text
gain_bytes = A_J - A_N
gain_B/M   = gain_bytes * 1,000,000 / 2,233,775
```

Authorize only one preregistered distant complete-block replay when:

```text
gain_B/M >= 3,000
```

A valid result below the threshold is `REJECT` with process status zero. It
retires this exact full-dictionary LibNC CPU mature-teacher lane without thread,
model, dictionary, checkpoint, precision, batch, block, or window rescue
sweeps. Nonzero process status is reserved for malformed evidence, missing
artifacts, broken identity, invalid probability conversion, failed decode,
memory failure, or infrastructure interruption.

A pass still authorizes no quotient, decoder, native integration, source
accounting, forecast credit, 100M, or 1G.
