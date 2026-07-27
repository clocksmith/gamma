# PPC-1: Polyhedral Probability-Cell Transfer

## Given

Let `Sigma` be a finite alphabet. A deterministic arithmetic coder has state
`c_t`, integer frequency input `f_t` from a finite set `F`, symbol input
`x_t`, deterministic transition

```text
(emitted_bytes, c_{t+1}) = A(c_t, f_t, x_t),
```

and deterministic finalizer `Z`.

Let

```text
Q : R^d -> F
```

be a deterministic probability quantizer. For every `f in F`, its cell is
given by a finite rational polyhedron with explicitly strict or non-strict
faces:

```text
C_f = {z : a_j . z < b_j for j in S_f,
             a_j . z <= b_j for j in N_f}.
```

A teacher predictor `T` and a decoder-recomputable student predictor `S`
consume the already decoded prefix. For each target prefix `x_{<t}`, a rational
axis-aligned box

```text
B_t = product_i [l_{t,i}, u_{t,i}]
```

is certified to contain `S(x_{<t})`.

## Questions

1. Give an exact rational test for `B_t subset C_f`.
2. Prove that the test is necessary and sufficient for containment of a box
   in the supplied half-space presentation.
3. If `T(x_{<t}) in C_{f_t}` and `B_t subset C_{f_t}` for every target
   position, prove teacher and student encoders emit identical archives.
4. Prove that the student decoder reconstructs the target from the teacher
   archive, even though the teacher is absent at decode time.
5. Include coder finalization and prove byte-for-byte archive equality.
6. Construct a finite certificate and deterministic verifier using only exact
   integer arithmetic.
7. Distinguish a corpus-specific prefix certificate from a universal
   all-input equivalence proof.
8. State the additional evidence required to transfer an under-target teacher
   into a Hutter-eligible CPU implementation.

## Frozen transfer target

The intended instance is a same-domain Compact5 NNCP student. Teacher and
student operate on the exact reversible NNCP symbol stream. The final student
must be deterministic, decoder-visible, self-contained, CPU-only, and
resource-eligible. Until a real teacher trace, compiled student, cell
certificate, native archive, and full score receipt exist, PPC-1 has zero
compression credit.
