# ROCm Batched Causality Repair Plan

Status: PASS - batched teacher headroom receipt authorized

Score credit: zero

## Correction under test

The prior batched NNCP-like ROCm path was rejected after changing input position
9 changed output position 9. That is not a future-leakage test when model inputs
are shifted:

```text
input[0] = BOS
input[t] = target[t - 1], t > 0
```

Changing `target[8]` changes `input[9]`. Prediction 9 may therefore change,
because target 8 has already been decoded. Predictions 0 through 8 must not
change.

This diagnostic does not reopen LibNC parity or claim a constructive decoder.
It tests only whether the existing batched ROCm teacher is causally legal as an
offline source of probability evidence.

## Fixed audit

Using the frozen 20-layer ROCm teacher architecture and the first 64 official
preprocessed symbols:

1. Construct `input_a = BOS || target_a[:-1]`.
2. Change only `target_b[8]`.
3. Construct `input_b = BOS || target_b[:-1]`.
4. Evaluate each complete shifted segment in one masked forward pass.
5. Require exact equality of logits at output positions 0 through 8.
6. Record, but do not gate on, the change at output position 9.
7. Compare batched and one-token-at-a-time execution as a separate numerical
   diagnostic.

## Decision

```text
PASS:
    maximum absolute batched prefix error at outputs 0..8 == 0
    and the algebraic dependency graph excludes all future inputs

REJECT:
    either condition fails
```

A pass authorizes one new zero-credit batched teacher headroom receipt. It does
not authorize a student, forecast movement, or native integration.

A rejection closes the batched ROCm teacher unchanged.

## Result

Job `20260728T190454Z_29f61f6127` passed:

```text
mask dependency graph isolated                 true
maximum prefix error, outputs 0 through 8      0.0
legal output-9 change                          1.046875
batched/incremental maximum logit drift        0.0078125
batched/incremental maximum probability drift  9.886134648695588e-7
```

The prior batched-teacher rejection was an off-by-one causality audit error.
The batched execution is authorized as a zero-credit offline teacher. The
batched/incremental drift prevents any constructive decoder claim.
