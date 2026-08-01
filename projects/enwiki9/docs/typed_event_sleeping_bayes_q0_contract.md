# Typed Event Sleeping Bayes Q0 Contract

Candidate: `typed_event_sleeping_bayes_envelope_q0_v1`

This file freezes the first opening-1M realization before its frontier P1
trace or chronological confirmation economics are read.

## Population

- Raw input: canonical opening 1,000,000 bytes.
- Coded truth: exact endpoint428 WRT stream.
- Pages: receipt-bound complete-page map.
- Development: first 60 percent of complete pages.
- Selection: next 20 percent.
- Sealed confirmation: final 20 percent.
- Model state: continuous across the complete WRT stream; diagnostic range
  payloads terminate independently by split.
- No page, block, or split model reset.

## Causal event unit

An opportunity begins before the first bit of each WRT event after the fixed
six-byte WRT header. WRT event length is discovered only from completed bytes:

```text
literal/control/one-byte token    1 byte
escape                            2 bytes
two-byte token                    2 bytes
three-byte token                  3 bytes
```

The current code, decoded raw bytes, event length, and terminal boundary do not
enter any key before they are complete. The completed event is inserted only
after all its bytes have been reconstructed.

## Frozen table and key geometry

```text
raw suffix bytes                         32
suffix hash                              FNV-1a 32-bit
Wiki schema hash                         FNV-1a 16-bit
maximum table keys                       50,000
maximum distinct codes per key           32
minimum aggregate opportunity support     4
maximum candidates per opportunity        16
candidate order                           descending count, then code bytes
key eviction                              FIFO insertion order
new code beyond per-key cap               reject
entity prefix                             last 8 completed WRT events
structural chains                         last 2 and last 4 events
literal prior weight                      65,536
candidate weight                          aggregate completed count
```

The literal branch is the exact endpoint428 conditional distribution. Each
deterministic candidate is a point mass on one previously completed WRT event
code. At prefix length `k`, surviving candidate weights remain unchanged and
the literal mass is multiplied by the exact B likelihood of the completed
prefix. The next-bit probability is the exact rational mixture rounded once to
nearest, ties upward, then clamped to `[1, 65535]`.

## Variant keys

```text
E0  suffix hash
E1  E0 plus (Wiki field, mode, slot, schema hash)
E2  E1 plus title/link receipt prefix while inside a captured entity
E3  E2 plus field-conditioned 2-event and 4-event structural chains
```

Keys are cumulative. Counts from multiple matching keys add; duplicate event
codes merge before ranking and the 16-candidate cap.

`C0` receives exactly the E3 opportunity/no-op decision, candidate count, and
sorted candidate weights. It replaces candidate codes with unique completed
codes from the global causal reservoir using frozen indices
`event_index*17 + rank*7919`, wrapping and scanning forward on collisions. It
therefore matches capacity and opportunity timing while destroying typed
alignment without reading future data.

## Outer mixtures and selectors

```text
M0 initial sequence weights       B=65,535, E3-star=1
M0 arithmetic                     float64 normalized every bit
M1 posterior total                2^24
M1 initial weights                exact 65,535:1 projection
M1 update                         multiply by realized Q16 likelihood
M1 renormalization                every 8 bits
M1 projection                     positive Hamilton remainder, expert ID tie
S0                                one global mode, B tie preference
S1 WRT block bytes                65,536
S1 payloads                       independently terminated per block
S1 mode stream                    adaptive binary range code, counts start 1:1
S1 framing                        magic, block count, mode length, block lengths
```

All B and E states update on every actual bit. M0 and M1 are probability
envelopes over the same sequence. S0 and S1 explicitly transmit their choices.

## Accounting

- Construct and terminate every reported arithmetic payload.
- Count actual S0/S1 control and framing bytes.
- Frozen projected decoder/source allowance: 98,304 bytes.
- Projected package charge at 1G: 98.304 B/M plus actual fixed framing.
- Dynamic decoder-built table state is memory, not transmitted package data.
- Report table bytes conservatively and require total measured process memory
  below the decimal 10GB limit at native integration.

## Promotion and kill rule

The primary decision model is M1. Authorize one distant 1M replay only if:

```text
parent payload replay                         byte-identical
independent frontier P1 traces                byte-identical
M1 arithmetic decode                         exact
decoded WRT and official raw inverse          exact
second causal M1 P1 and payload               byte-identical
development M1 gain                          positive
selection M1 gain                            positive
sealed M1 gross gain                         >= 3,000 B/M
sealed M1 package-adjusted gain               >= 2,100 B/M
sealed E3 advantage over C0                   >= 256 B/M
M1 loss versus positive M0 ideal gain         < 5 percent
positive sealed quartiles                     at least 3 of 4
largest sealed positive quartile share        <= 60 percent
all probability values                        legal and nonzero
```

A miss retires this exact event unit, key family, table geometry, literal
prior, Bayes precision, selector block, and associated parameter rescue
sweeps. A valid compression rejection exits zero. Identity, causality,
determinism, inverse, missing-input, or illegal-probability failures exit
nonzero.
