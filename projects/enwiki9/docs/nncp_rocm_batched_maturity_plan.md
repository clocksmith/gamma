# ROCm Batched Teacher Maturity Plan

Status: Q1 500K gate authorized

Score credit: zero

## Evidence entering Q1

The shifted-input batch causality audit passed exactly. The 65,536-symbol Q0
teacher also passed deterministic double execution, trace-driven arithmetic
reconstruction, symbol identity, and the official inverse.

At the exact shared 322,978-raw-byte boundary:

```text
Gamma                         468,490.156 bits
ROCm teacher                  727,447.033 bits
teacher minus Gamma           -32,369.610 bytes
```

This is a severe startup deficit. It does not by itself test whether online
learning has reached a useful marginal regime.

## Q1

Run the same frozen architecture and update schedule from symbol zero through:

```text
teacher symbols               102,871
exact mapped raw boundary      500,000
```

Q1 is a single-pass diagnostic. It must still pass:

```text
shifted-input prefix causality
trace-driven arithmetic reconstruction
symbol identity
official raw inverse
ROCm memory receipt
```

The existing Q0 double execution already establishes deterministic behavior for
the same code path. Q1 receives no determinism or score claim.

## Marginal decision

Let `G(b)` be Gamma bits minus teacher bits through raw boundary `b`.

```text
marginal gain =
    G(500,000) - G(322,978)
```

Authorize a 1M maturity receipt only when:

```text
marginal gain > 0
and
marginal gain / (500,000 - 322,978) >= 3,000 B/M
```

If the marginal band is non-positive, reject this ROCm teacher unchanged. Do not
alter width, depth, vocabulary, precision, learning rate, optimizer, memory, or
segment length.
