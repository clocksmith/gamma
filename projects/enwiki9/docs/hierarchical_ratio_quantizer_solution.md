# HRQ-1: Complete Solution

## Unique branch path

At each node the active integer interval

```text
[start, start + range)
```

is partitioned into the disjoint left interval of length `floor(range/2)` and
the remaining right interval. Bit `b` selects the unique child containing
`s`. The active interval strictly shrinks while its length exceeds one, so the
process terminates at `[s,s+1)`.

Induction on the split depth proves both existence and uniqueness. Conversely,
replaying a valid branch sequence from `(0,n)` reaches exactly one singleton,
which recovers the symbol.

## Exact split count

The sequence is constructed deterministically by:

```text
while range > 1:
    left = floor(range/2)
    bit = 1{s >= start + left}
    if bit:
        start += left
        range -= left
    else:
        range = left
```

Its length is either `floor(log2 n)` or `ceil(log2 n)`, depending on the leaf
depth in the fixed nearly balanced tree. The algorithm itself is the exact
answer for every non-power-of-two `n`.

## Archive and decoder transfer

Suppose teacher and student coders begin in the same state and receive the same
symbol. At every visited split they receive the same integer `q` and the same
branch bit. Determinism of `put_bit` gives identical emitted bytes and next
coder states. Induction over branches, then symbols, and finally coder
finalization proves byte-identical archives.

For decoding, assume the student has reconstructed the prior symbol prefix. It
recomputes its state and predicts `q` for the current split. The arithmetic
decoder returns the same branch bit used by the teacher archive. Replaying the
split reaches the same symbol, which extends the induction. The teacher and its
full distribution are unnecessary at decode time.

## Rational ratio cells

With nonnegative masses and `0<c<=p<=d`,

```text
a/d <= p0/p <= b/c.
```

For an interior unclamped frequency `1 < q < M-1`, strict containment in the
nearest-integer cell is certified by

```text
(q - 1/2)/M <  a/d
and
b/c < (q + 1/2)/M.
```

Cross-multiplying positive denominators makes both checks exact over integers.
Strict inequalities deliberately exclude floating tie cases and are therefore
sufficient under every nearest-rounding tie convention.

The lower clamp cell `q=1` is certified when

```text
b/c < (3/2)/M.
```

Every rounded value at or below one then clamps to one. The upper clamp cell
`q=M-1` is certified when

```text
(M - 3/2)/M < a/d.
```

Every rounded value at or above `M-1` then clamps to `M-1`. These are robust
sufficient conditions, not necessary characterizations of boundary ties.

## Compact trace

For each symbol, record:

```text
execution index
coder count before and after
symbol
vocabulary size
branch count
for every branch:
    uint16 q
    uint8 bit
```

The verifier reconstructs the unique split path from the symbol and vocabulary,
checks every bit, checks `1<=q<M`, verifies consecutive execution indices and
coder-count continuity, and rejects trailing bytes. Trace-on and trace-off
archives must have equal lengths and hashes.

## Transfer boundary

The trace supplies exact student targets and a closure certificate. It does not
construct a compact causal student. Score credit additionally requires:

1. a decoder-recomputable student with fully counted source and model;
2. exact archive replay on chronological and distant gates;
3. full-corpus score at or below the target;
4. deterministic roundtrip;
5. official CPU runtime, memory, disk, and no-GPU eligibility.
