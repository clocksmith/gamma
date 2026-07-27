# FP-1 Solution: Fingerprint-Capacity Packing

## 1. Exact feasibility

Because \(Q\) is a multiple of 32,

\[
C(A,b)\le Q
\]

is equivalent to

\[
R(A,b)\le Q.
\]

Substituting the raw size gives

\[
\left\lceil\frac{Ab}{8}\right\rceil\le Q-7A-1.
\]

The right side is an integer. For an integer \(L\),

\[
\left\lceil\frac{x}{8}\right\rceil\le L
\quad\Longleftrightarrow\quad
x\le8L.
\]

Therefore

\[
Ab\le8(Q-7A-1),
\]

or equivalently

\[
\boxed{A(b+56)\le8(Q-1).}
\]

This condition is both necessary and sufficient; it contains no alignment
relaxation.

## 2. Maximum associativity and width

For fixed \(Q\) and \(b\), feasibility is monotone in \(A\), so

\[
\boxed{
A_{\max}(Q,b)=
\left\lfloor\frac{8(Q-1)}{b+56}\right\rfloor.
}
\]

For fixed \(Q\) and \(A\), rearranging the same inequality yields

\[
b\le\frac{8(Q-1)}{A}-56.
\]

Thus the largest nonnegative integer width is

\[
\boxed{
b_{\max}(Q,A)=
\left\lfloor\frac{8(Q-1)}{A}\right\rfloor-56.
}
\]

If this quantity is negative, no positive fingerprint width fits.

## 3. Sixteen-bit frontier

With \(b=16\),

\[
A_{\max}(Q,16)=
\left\lfloor\frac{8(Q-1)}{72}\right\rfloor.
\]

Hence:

| \(Q\) | \(A_{\max}(Q,16)\) |
|---:|---:|
| 32 | 3 |
| 64 | 7 |
| 96 | 10 |
| 128 | 14 |

These are exactly the four undominated associativities found by AF-1 for the
existing two-byte fingerprint representation.

## 4. The 96-byte alternatives

For \(Q=96\) and \(A=11\),

\[
b_{\max}(96,11)
=
\left\lfloor\frac{760}{11}\right\rfloor-56
=69-56
=13.
\]

Therefore

\[
\boxed{C(11,b)\le96\iff b\le13.}
\]

At \(b=13\), the packed fingerprints use

\[
\left\lceil\frac{11\cdot13}{8}\right\rceil
=18
\]

bytes, and

\[
R(11,13)=77+1+18=96.
\]

The fit is exact.

For \(A=12\),

\[
b_{\max}(96,12)
=
\left\lfloor\frac{760}{12}\right\rfloor-56
=63-56
=7.
\]

Thus twelve ways do fit when \(b=7\), exactly:

\[
R(12,7)=84+1+\lceil84/8\rceil=96.
\]

Accordingly, the proposed clause claiming that twelve ways cannot fit even at
seven bits is false. Its explicit counterexample is

\[
\boxed{(A,b,Q)=(12,7,96).}
\]

The corrected boundary is:

\[
C(12,b)\le96\iff b\le7.
\]

This counterexample is part of the complete solution rather than a reason to
discard the problem.

## 5. False-match probability

Fix a query for a key absent from the bucket. Under the stated independent,
uniform model, one resident fingerprint fails to equal the query with
probability

\[
1-2^{-b}.
\]

All \(A\) resident fingerprints avoid the query with probability

\[
(1-2^{-b})^A.
\]

Therefore the exact probability of at least one false fingerprint match is

\[
\boxed{
p_{\mathrm{false}}(A,b)
=1-(1-2^{-b})^A.
}
\]

The union bound gives

\[
\boxed{
p_{\mathrm{false}}(A,b)\le A2^{-b}.
}
\]

The exact expression needs independence among resident fingerprints. The union
bound only needs each resident comparison to have collision probability at
most \(2^{-b}\); the collision events need not be mutually independent.

## 6. Ten-wide versus eleven-wide

For \((A,b)=(10,16)\),

\[
p_{\mathrm{false}}
=1-(1-2^{-16})^{10}
\le\frac{10}{65536}
\approx1.52588\times10^{-4}.
\]

For \((A,b)=(11,13)\),

\[
p_{\mathrm{false}}
=1-(1-2^{-13})^{11}
\le\frac{11}{8192}
\approx1.34277\times10^{-3}.
\]

The ratio of the union-bound ceilings is

\[
\frac{11/8192}{10/65536}
=\frac{88}{10}
=8.8.
\]

Thus the eleven-way layout retains ten percent more ways than the ten-way
layout at the same 96-byte cell size, but its conservative false-match ceiling
is 8.8 times larger. Neither layout dominates the other in the
capacity/reliability plane.

The twelve-way, seven-bit layout raises capacity another \(12/11\), but its
union-bound ceiling is

\[
\frac{12}{128}=0.09375,
\]

which is too large to treat as a reliability-preserving substitute without
native evidence.

## 7. Canonical packing

Number the ways \(0,\ldots,A-1\). Store fingerprint \(j\) in bit positions

\[
jb,\ldots,(j+1)b-1
\]

of a little-endian packed fingerprint bit string. Reads mask exactly \(b\)
bits; writes clear and replace exactly those bits. Encoder and decoder use the
same integer shifts and masks, so equal prior state and equal decoded symbols
imply equal table state by induction.

This proves deterministic representation semantics. It does not prove that
truncating a sixteen-bit hash to \(b\) bits preserves predictions.

## 8. Transfer boundary

FP-1 licenses two predeclared 96-byte alternatives:

- ten ways with sixteen-bit fingerprints;
- eleven ways with thirteen-bit fingerprints.

The first preserves fingerprint width and reduces associativity. The second
trades a wider collision surface for one additional way. Native testing must
measure the complete effects of replacement, collision, mixer feedback, and
coder finalization.

A transferable receipt still requires:

- exact source and package bytes;
- exact archive bytes from joint native replay;
- exact reconstruction and deterministic second archive;
- decimal-10GB peak memory;
- runtime eligibility;
- transfer and full-scope gates.

No probability bound in this solution is compression credit.

