# PPC-1: Complete Solution

## Exact box containment

For a rational linear form

```text
a . z = sum_i a_i z_i
```

on the box `B = product_i [l_i, u_i]`, its maximum is

```text
M_B(a) =
  sum_{a_i >= 0} a_i u_i
  + sum_{a_i < 0} a_i l_i.
```

This follows because every coordinate is independent and a linear term is
maximized at its upper endpoint for nonnegative coefficient and at its lower
endpoint for negative coefficient.

Therefore:

```text
B subset {z : a.z <= b} iff M_B(a) <= b,
B subset {z : a.z <  b} iff M_B(a) <  b.
```

Applying this test to every face is necessary and sufficient for
`B subset C_f`. All inputs are rational, so cross-multiplication or normalized
rational arithmetic decides every comparison exactly.

## Encoder equality

Use induction on the target position. Initially both coders have the same
state. At position `t`, the teacher output belongs to `C_{f_t}`. The certified
student box is contained in that same cell, so

```text
Q(S(x_{<t})) = f_t = Q(T(x_{<t})).
```

Both coders receive the same state, frequency object, and target symbol.
Determinism of `A` gives identical emitted bytes and identical next coder
states. The induction covers the complete target. Equal final states passed to
the deterministic finalizer `Z` emit identical terminal bytes. The complete
archives are byte-identical.

## Decoder equality

The student decoder begins with the common initial coder state and empty
prefix. Assume it has reconstructed `x_{<t}`. It recomputes `S(x_{<t})`, which
the certificate places in the teacher cell `C_{f_t}`. It therefore supplies the
same integer frequency object used to encode the next symbol. Arithmetic
decoding returns `x_t` and the same next coder state. Induction reconstructs
the complete target without evaluating or shipping the teacher.

The certificate is proof evidence, not decoder payload. The decoder needs only
the student.

## Certificate

A finite corpus certificate contains:

```text
target hash
coder and quantizer hashes
teacher frequency-cell identifier at every position
student rational box at every position
all rational cell faces
student source and model hashes
archive hash
```

The verifier validates every rational interval, computes every face maximum,
checks strictness exactly, then performs native student decode and re-encode.

A prefix certificate proves equality only on the committed target trajectory.
A universal proof must establish the same cell containment for every reachable
prefix, usually through an inductive state invariant. The corpus-specific
certificate is sufficient to prove the submitted enwik9 archive, but it does
not imply general predictor equivalence.

## Hutter transfer boundary

To transfer an under-target teacher, the organizer must additionally provide:

1. an exact teacher archive and complete counted score;
2. an exact reversible symbol representation;
3. a compiled student and cell certificate on every coded position;
4. a self-contained counted student package;
5. exact roundtrip and deterministic second-archive receipts;
6. official CPU runtime, memory, disk, and no-GPU eligibility.

PPC-1 removes floating-probability equality as a requirement. It does not
construct the student, establish teacher headroom, or prove resource
eligibility.
