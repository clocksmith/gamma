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
reconstructive source package  280,147 bytes  19ddcc4ec1b6f31958bed4aa19c0fbc83a56c78121933e1447e4ee011547aee0
minified counted package       261,125 bytes  b6fe6b09d6adbd8a287a08d284ca1f439ba72ff007b4d40c66bf7647a54a5d43
wrapper                      2,326,416 bytes  37ee8cd73ade9845b1afcb39f3bbd9358956c3ff9aea3b69328da7441ee32361
backend                      1,899,840 bytes  d1066630f0d58894e69bd84519ec7d0f608b9e2fce67ab9ebedde65c58eca194
dictionary                     411,996 bytes  4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
```

The two source hashes have different proof roles. `19dd...` is the original
reconstructive package whose two bundles reproduce the same 102 source files
and whose two clean builds emit the bound wrapper and backend. `b6fe...` is the
comment-stripped package whose independent clean builds emit those same binary
hashes and whose 19,022-byte reduction supplies the current `109,389,323`
forecast. Recovering or naming only one is insufficient: native instrumentation
must be traceable to the reconstructive source identity, while final child
accounting must compare against the minified counted identity.

The recovered source seam is `build/src/predictor.cpp` at
`Predictor::Predict()` and `Predictor::Perceive(int)`, with the asynchronous
endpoint in `build/src/fx2lite/endpoint428.cpp` at `Endpoint::PredictSync()` and
`Endpoint::PerceiveSync(int)`. A harness receipt must name the exact recovered
bundle used to materialize this tree, its pre-edit source hash, the canonical
child diff, and the resulting child package hash. The parent `b6fe...` package
does not reconstruct or pay for the modified child merely because it builds the
unchanged parent binary.

## Dual execution

Run the literal control and bypass child in separate clean processes. Do not
instantiate two parent predictors in one process: compact FXCM and the renamed
FX2 FXCM keep extensive namespace-global mutable state, so two objects would
cross-contaminate and invalidate the comparison.

Bind identical vocabulary extraction, the six-byte stored WRT header,
dictionary pretraining, source/backend configuration, and event schedule. The
counted minified ZIP identifies the unchanged parent accounting baseline, not
the modified child; also bind the child diff and child compressed-package hash.

The exact native seam is the existing two-call transition:

```text
literal control bit:
    p = Predictor.Predict()
    b = ParentArithmetic.Decode(p)
    Predictor.Perceive(b)

bypass bit:
    p = Predictor.Predict()
    discard p for parent arithmetic consumption
    b = reconstructed exact event bit
    Predictor.Perceive(b)
```

There is no `PerceiveAndUpdate(p, b)` interface: prediction-to-update caches are
internal. The bypass path must execute the same `Predictor::Predict()` and
`Predictor::Perceive(bit)` calls, in MSB-first WRT-store bit order, while
omitting only the parent arithmetic interval/renormalization step. Calling
`ContextManager::UpdateContexts`, an endpoint-only update, or any partial truth
injection is invalid.

The least invasive first certificate records the discretized parent P1 before
every truth bit in each isolated process. Require the literal and bypass P1
streams to be byte-identical over the complete gate, with exact WRT/raw replay.
Identical initialization, identical truth, and literally identical deterministic
transition calls give an induction proof of parent-state equality; component
digests below are defense-in-depth against an incorrect native seam.

## Hash boundary

FX2 endpoint work is asynchronous. `Endpoint::Perceive` queues a bit and
returns; hashing immediately afterward races `PerceiveSync` and the next
`PredictSync`. Do not join the worker at checkpoints because join terminates
the endpoint. At each completed bypass event, page close, and final population:

1. Call the next ordinary `Predictor::Predict()`. It waits for FX2 readiness and
   establishes the next compact prediction caches. Retain that returned P1 for
   the next truth bit; never call Predict twice for one bit. At final EOF, make
   one symmetric unused Predict in both processes or add a wait-only quiesce
   hook.
2. Canonically serialize logical predictor state with fixed integer widths and
   byte order.
3. Hash the child incremental WRT-event parser, Wiki parser, and decoder-built
   graph state separately.
4. Compare the literal and bypass hashes.

The parent hash must cover:

- every ContextManager scalar, history, word/recent-byte buffer, mutable context
  table, stack, hash, and vector state;
- Direct, DirectHash, Indirect, Match, Bracket, ByteModel, ByteMixer, main FXCM,
  and renamed FX2 FXCM mutable state, outputs, predictions, counts, maps, match
  buffers, parser scalars, and caches;
- both PPMD allocator arenas, free lists, contexts/statistics, masks, run/order
  state, prepared-byte caches, and active pointers serialized as arena offsets;
- every mixer input, context entry, weights, steps, probability and active
  prediction cache; serialize active entries by canonical keys, never pointers;
- complete recurrent input/history/state/error/weight/optimizer/normalization
  arrays and all forward/update caches;
- SSE and adaptive calibration tables plus Predict-to-Perceive active caches;
- online residual global/local/regret/seen/features/context/base/hypothetical
  state; and
- FX2 logical phase flags, pending bit, cached prediction, bit context, and
  complete asynchronous endpoint state after quiescence.

Sort unordered maps and encode all lengths and keys. Hash exact float bit
patterns and logical integer values, not object bytes. Normalize every logical
pointer to a stable table, context key, or arena offset. Immutable derived
lookup tables and vocabulary may be bound once by source/config/dictionary
hash rather than repeated at every checkpoint.

The current endpoint has no native WIKI-JOINT graph or incremental official WRT
inverse. ContextManager's WRT-like contexts remain parent state, while the
child's `WrtDecoderState`, Wiki state, page machine, and graph require separate
native implementation and digest. The official `preprocessor::Decode` runs only
after the complete WRT temp stream is reconstructed.

Exclude the parent arithmetic-coder interval/output buffer and the child's
side/rank coder, residual input cursor, and framing state. Those must differ
because bypass omits parent truth decisions. Archive equality is checked within
each execution mode, not between literal and bypass archives. Thread, mutex,
condition-variable, address, padding, clock, and file-descriptor bytes are also
nonlogical and forbidden from the digest.

## Fail-closed controls

Require:

```text
literal versus literal repeated run            all hashes identical
bypass versus bypass repeated run              all hashes identical
literal versus bypass                          all logical hashes identical
one deliberately corrupted reconstructed bit  next quiescent mismatch exact
one deliberately skipped Predict call          fail-closed abort at injected row
WRT/raw reconstruction                         exact
second bypass archive                          byte-identical
```

Any missing state surface, nondeterministic quiescence, or mismatch is malformed
proof evidence and exits nonzero. It cannot become a scientific compression
rejection.

The existing WIKIBACK final digest is not this state certificate: it omits the
live PageStage, Wiki state, active snapshots, global tail, and live counters.
Extend or replace it for native event-boundary comparison.

## Activation

Do not implement or run this harness speculatively. Activate it only for the
first WIKIBACK, WIKISECTION, WIKIFORWARD, or later joint child whose actual
finite side/residual gate passes. Bind that lane's exact event schedule and
native source delta, then require state equality before distant, 100M, forecast,
or full-1G promotion.

This harness does not solve endpoint428 runtime. Prediction and update still
execute for bypassed bits, so runtime qualification remains an independent
score-terminal condition.
