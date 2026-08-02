# NNCP v3.3 LibNC CPU encode-only mature 9M-10M Q1

Candidate:
`nncp_v33_libnc_cpu_encode_only_mature_9m_10m_q1_v1`

## Claim boundary

This is a zero-credit teacher headroom gate. The upstream `--encode_only`
archive is not decodable and cannot become a Hutter score, forecast input, or
package claim. Q1 asks only whether the exact NNCP information source has
target-scale arithmetic headroom on a mature population when run continuously
from symbol zero with the full frozen dictionary.

The canonical score boundary remains:

```text
target                         108,000,000 bytes
verified full-1G result        unknown
best counted forecast          109,389,323 bytes
remaining forecast debt          1,389,323 bytes
new score credit                         0 bytes
```

## Authorized population

Q0 authorizes one execution through the frozen mature window in
`results/nncp_full_symbol_map_v1/window_manifest.json`:

```text
window                         mature_9m_10m
raw interval                   [9,000,000, 9,999,992)
raw bytes                      999,992
NNCP symbol interval           [2,000,597, 2,229,154)
execution prefix               [0, 2,229,154)
```

The teacher may use only the frozen NNCP v3.3 source package, dictionary,
preprocessed symbol stream, and completed causal prefix. It must execute from
symbol zero. No warm-start state, reset window, alternate dictionary, model,
thread count, batch layout, precision, or checkpoint is permitted.

## Same-population parent

The comparison parent is the exact exported JANUS-plus-quotient joint P1
trajectory. The WRT inverse must place both raw boundaries on exact completed
emission-group boundaries. The corresponding bit prefixes are terminated and
decoded independently:

```text
raw 9,000,000                 WRT byte 5,622,906
raw 9,999,992                 WRT byte 6,251,844
joint bit interval            [44,983,248, 50,014,752)
```

The parent window charge is an actually terminated arithmetic stream containing
only the joint-P1 truth bits in that exact WRT interval. The teacher charge is
an actually terminated stream containing only NNCP branch decisions whose
frozen original symbol ordinals fall in the exact NNCP interval. Both use the
same finite range coder and both are decoded exactly. Neither lane may use
log-loss estimates or prefix-size subtraction.

## Observer and integrity contract

Build the consumed-branch observer from the immutable source tarball. Before
the mature execution, run a 10,000-symbol full-dictionary smoke with the
receipt-bound original binary, the patched binary with observation disabled,
and the patched binary with observation enabled. All three archives must be
byte-identical. The observed smoke trace must contain legal nonzero integer
probabilities, an exact permutation of original symbol ordinals, and an exact
finite subset-stream decode.

The mature execution then runs once with observation enabled through symbol
`2,229,154`. Its observer records the original preprocessed ordinal attached to
every branch path. It must satisfy:

```text
source, dictionary, input, map identities       exact
Q0 authorization                                PASS
continuous execution from symbol zero           required
small observer neutrality                       exact
original ordinal permutation                   exact
selected ordinals [2,000,597, 2,229,154)       exact
consumed branch paths                           exact
integer probabilities                           1..32767
trace structure and counts                      exact
process-tree peak RSS                           <= 9,765,625 KiB
joint and teacher window arithmetic decode      exact
```

The teacher archive itself remains non-decodable; `roundtrip_ok` is therefore
not asserted. Q0 already established causal full-distribution semantics and a
future-symbol perturbation invariant for this encode-only execution schedule.

## Decision

Let `A_J` be the exact joint-parent window stream and `A_N` the exact native
teacher window stream across the identical `999,992` raw bytes:

```text
gain_bytes = A_J - A_N
gain_B/M   = gain_bytes * 1,000,000 / 999,992
```

Authorize only the frozen `49M-50M` continuation when:

```text
gain_B/M >= 3,000
```

A valid result below the threshold is `REJECT` with process status zero. It
retires this full-dictionary LibNC CPU encode-only mature-teacher lane without
thread, model, dictionary, checkpoint, precision, batch, observer, or window
rescue sweeps. A nonzero process status is reserved for malformed evidence,
missing artifacts, broken identity, invalid probabilities, failed arithmetic
decode, memory failure, or infrastructure interruption.

A pass does not authorize a quotient, native integration, source accounting,
forecast credit, 100M, or 1G. It authorizes only one continuous execution to
the already frozen `49M-50M` window.
