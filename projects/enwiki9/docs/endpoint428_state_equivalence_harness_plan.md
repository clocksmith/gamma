# Endpoint428 State-Equivalence Harness Plan

Status: reusable proof infrastructure, zero score credit, no candidate or job.
Implement against the recovered exact endpoint428 source only after a frozen
WIKI event lane passes its trace-level paid gate.

## Purpose

Prove that state-preserving bypass is native reality rather than a P1-trace
assumption. A literal parent execution and a bypass execution must expose the
same reconstructed WRT bits to every predictor and parser transition while
only the arithmetic-coder interval/output state differs.

Bind the parent identities:

```text
minified source package  b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43
wrapper                  37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361
backend                  d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194
dictionary               4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
```

## Dual execution

Start two clean parent instances from identical source and state.

```text
literal control bit:
    p = Parent.Predict()
    b = ParentArithmetic.Decode(p)
    Parent.PerceiveAndUpdate(p, b)

bypass bit:
    p = Parent.Predict()
    discard p for parent arithmetic consumption
    b = reconstructed exact event bit
    Parent.PerceiveAndUpdate(p, b)
```

The bypass path must call the same prediction transition because endpoint428
may cache forward values used by learning. Directly injecting truth into a
partial update routine is invalid.

## Hash boundary

At each bypassed bit, completed event, page close, and final population:

1. Quiesce or join all deferred endpoint work.
2. Canonically serialize logical predictor state with fixed integer widths and
   byte order.
3. Hash WRT state, Wiki parser state, and decoder-built graph state separately.
4. Compare the literal and bypass hashes.

The parent hash must cover PPM/PPMD, matches, context maps, FXCM, recurrent
state and weights, mixer inputs/weights, SSE/calibration, cached forward
values, learning counters, asynchronous endpoint buffers, and every pointer or
index whose logical value affects later prediction. Do not hash raw addresses,
padding, allocator metadata, thread handles, clocks, or file descriptors.

Exclude only arithmetic-coder interval, pending bits, and output buffers. Those
must differ because bypass omits truth decisions. Archive equality is checked
within each execution mode, not between literal and bypass archives.

## Fail-closed controls

Require:

```text
literal versus literal repeated run            all hashes identical
bypass versus bypass repeated run              all hashes identical
literal versus bypass                          all logical hashes identical
one deliberately corrupted reconstructed bit  first mismatch detected exactly
one deliberately skipped Predict call          mismatch detected exactly
WRT/raw reconstruction                         exact
second bypass archive                          byte-identical
```

Any missing state surface, nondeterministic quiescence, or mismatch is malformed
proof evidence and exits nonzero. It cannot become a scientific compression
rejection.

## Activation

Do not implement or run this harness speculatively. Activate it only for the
first WIKIBACK, WIKISECTION, WIKIFORWARD, or later joint child whose actual
finite side/residual gate passes. Bind that lane's exact event schedule and
native source delta, then require state equality before distant, 100M, forecast,
or full-1G promotion.

This harness does not solve endpoint428 runtime. Prediction and update still
execute for bypassed bits, so runtime qualification remains an independent
score-terminal condition.
