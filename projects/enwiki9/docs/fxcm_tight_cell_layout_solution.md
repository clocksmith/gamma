# Solution to SLC-1: Tight State-Cell Layout

## A. Exact layout

The `chk` array starts at offset \(0\), occupies \(2A\) bytes, and has
alignment two. The next available offset is already valid for `last`, so

\[
\operatorname{off}(\operatorname{last})=2A.
\]

The byte array `bh` requires only alignment one and therefore starts
immediately afterward:

\[
\boxed{
\operatorname{off}(\operatorname{chk})=0,\quad
\operatorname{off}(\operatorname{last})=2A,\quad
\operatorname{off}(\operatorname{bh})=2A+1.
}
\]

The logical fields end at

\[
2A+1+7A=9A+1.
\]

The record alignment is two, hence

\[
\boxed{
|\mathcal R_A|
=2\left\lceil\frac{9A+1}{2}\right\rceil.
}
\]

The union also has alignment two, and its largest member has unrounded size
\(\max(|\mathcal R_A|,B)\). Therefore

\[
\boxed{
|\mathcal E_{A,B}|
=2\left\lceil
\frac{\max(|\mathcal R_A|,B)}{2}
\right\rceil.
}
\]

For \(A=10\), the fields end at \(91\) and the record rounds to \(92\).
Consequently

\[
|\mathcal E_{10,96}|=96,
\qquad
|\mathcal E_{10,92}|=92.
\]

For \(A=14\), the fields end at \(127\) and the record rounds to \(128\), so

\[
|\mathcal E_{14,128}|=128.
\]

Any valid A10 union must contain the 92-byte logical record. Thus no width
below 92 is possible, and \(B=92\) attains the minimum.

## B. Array alignment and addressability

The array base is divisible by 128 and therefore by two. Every cell begins at

\[
\text{base}+92i.
\]

Since 92 is even, every cell base is divisible by two. Each checksum begins at
an even offset \(2j\), so all checksum addresses are 2-byte aligned.

The member offsets depend only on \(A\), not on the padding member. In both
layouts, `last` is at offset 20 and `bh` starts at offset 21. Every `bh[i][j]`
therefore has the same within-cell offset

\[
21+7i+j.
\]

Replacing \(N\) cells saves exactly

\[
\boxed{(96-92)N=4N\text{ bytes}.}
\]

## C. State equivalence

At time zero, corresponding logical fields and coder states are equal.
Assume equality before step \(t\). The common decoded history and state produce
the same table index. Corresponding logical fields at that index are equal, so
the common lookup and replacement rules choose the same slot and produce the
same integer probability.

Both arithmetic coders receive the same probability and symbol, hence make the
same transition. The common update rule writes equal values to corresponding
logical fields. Padding is never observed, so changing its extent cannot enter
the transition. The invariant holds before step \(t+1\).

By induction, all logical fields, probabilities, coder states, archives, and
decoded symbols are identical.

The proof fails if padding is read, raw records are serialized or compared,
addresses influence hashes or state, or the implementation ABI does not
satisfy the frozen size, alignment, and offset rules. Those behaviors add
observable state not represented by the logical fields.

## D. Dense reinvestment

With \(M=128N_0\),

\[
\boxed{
N_{96}
=\left\lfloor\frac{128N_0}{96}\right\rfloor
=\left\lfloor\frac{4N_0}{3}\right\rfloor,
}
\]

and

\[
\boxed{
N_{92}
=\left\lfloor\frac{128N_0}{92}\right\rfloor
=\left\lfloor\frac{32N_0}{23}\right\rfloor.
}
\]

Before flooring, the respective capacity ratios are \(4/3\) and \(32/23\).
Their difference is

\[
\frac{32}{23}-\frac43
=\frac{96-92}{69}
=\frac4{69}.
\]

Thus

\[
N_{92}-N_{96}
=
\left\lfloor\frac{32N_0}{23}\right\rfloor
-
\left\lfloor\frac{4N_0}{3}\right\rfloor.
\]

For arbitrary reals \(x,y\),

\[
x-y-1<\lfloor x\rfloor-\lfloor y\rfloor<x-y+1.
\]

Therefore the sharp uniform floor-error statement is

\[
\boxed{
\frac{4N_0}{69}-1
<
N_{92}-N_{96}
<
\frac{4N_0}{69}+1.
}
\]

The exact integer is given by the preceding difference of floors.

For width \(B\in\{92,96\}\), \(g\) guard cells, and \(a\) external alignment
bytes, total allocation is

\[
\boxed{
B\left(\left\lfloor\frac{M}{B}\right\rfloor+g\right)+a.
}
\]

Only the first \(\lfloor M/B\rfloor\) cells are indexable.

## E. Finite certificate

A source certificate defines both record unions and emits:

- `sizeof` and `alignof` for `U8` and `U16`;
- `offsetof(chk)`, `offsetof(last)`, and `offsetof(bh)`;
- `sizeof` and `alignof` for both unions;
- each checksum address modulo two in a finite test array;
- hashes of logical fields after an identical deterministic write sequence.

A verifier requires scalar sizes and alignments \(1,1,2,2\), offsets
\(0,20,21\), union sizes \(96,92\), even checksum addresses, and equal logical
hashes. The work is linear in the finite array length and write count.

This establishes the ABI antecedent and archive-identity theorem. It supplies
zero compression credit until an exact native candidate confirms identity and
a separately changed dense cell count improves total counted codelength.

