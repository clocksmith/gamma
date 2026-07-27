# HRQ-1: Hierarchical Ratio-Quantizer Transfer

## Given

Let `w_0, ..., w_{n-1}` be positive prediction weights. To code symbol `s`,
start with

```text
start = 0
range = n
p = sum_i w_i.
```

While `range > 1`, set

```text
range0 = floor(range / 2)
p0 = sum_{i=start}^{start+range0-1} w_i
q = clamp(round(M*p0/p), 1, M-1)
b = 1{s >= start + range0}.
```

Emit branch bit `b` with integer frequency `q`. If `b=0`, replace
`(range,p)` by `(range0,p0)`. If `b=1`, replace them by
`(range-range0,p-p0)` and increase `start` by `range0`.

For NNCP, `M=32768`, `round` is the frozen `lrintf` operation, and the integer
frequency is passed directly to `put_bit`.

## Questions

1. Prove that the branch-bit sequence uniquely identifies `s`.
2. Derive the exact number and sequence of range splits for every `(n,s)`.
3. Prove that reproducing the integer `q` at every visited branch is sufficient
   for byte-identical arithmetic coding, even if the student never reconstructs
   the full weight vector.
4. Prove teacher-free decoding when the student predicts each branch frequency
   causally from the decoded symbol prefix and current split state.
5. For rational intervals

   ```text
   p0 in [a,b], p in [c,d], 0 < c <= d,
   ```

   derive sufficient exact inequalities certifying an unclamped integer
   frequency `q`.
6. Treat the two clamp cells `q=1` and `q=M-1`.
7. Construct an archive-neutral compact trace containing symbol identity,
   coder counts, branch bits, and integer frequencies.
8. Give a deterministic verifier for trace syntax, split-path correctness,
   coder-count continuity, and trace-on/trace-off archive identity.
9. State what remains before a branch-frequency student can receive Hutter
   score credit.

## Frozen transfer target

The target is Compact5 NNCP in its native reversible preprocessed symbol
domain. A student may predict the visited branch frequencies directly. It need
not emit 336-way or larger floating distributions. Exact native score and
resource gates remain authoritative.
