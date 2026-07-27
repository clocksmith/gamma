# Solution to DRB-1: Dense Range Buckets

## A. Dense allocation

Every complete cell consumes \(B\) bytes. Thus \(C\) cells fit exactly when
\(BC\le M\), and the largest such integer is

\[
\boxed{C(M,B)=\lfloor M/B\rfloor.}
\]

Euclidean division gives

\[
M=B\lfloor M/B\rfloor+(M\bmod B),
\qquad 0\le M\bmod B<B,
\]

so the unused budget is exactly \(M\bmod B\).

For \(M=128\cdot2^k\) and \(B=96\),

\[
\boxed{
N_1=\left\lfloor\frac{128\cdot2^k}{96}\right\rfloor
=\left\lfloor\frac{4\cdot2^k}{3}\right\rfloor.
}
\]

Writing \(N_0=2^k\),

\[
\frac{N_1}{N_0}
=
\frac{\lfloor4N_0/3\rfloor}{N_0}
\ge
\frac43-\frac1{N_0}.
\]

The strict floor error is less than one cell, so this is sharp as a uniform
bound. Since powers of two are never divisible by three, the ratio is always
strictly below \(4/3\), with deficit either \(1/(3N_0)\) or \(2/(3N_0)\).

If \(g\) guard cells and \(A\) alignment bytes are outside the usable budget,
the total allocation is

\[
\boxed{
B\bigl(\lfloor M/B\rfloor+g\bigr)+A,
}
\]

while exactly \(\lfloor M/B\rfloor\) cells are indexable.

## B. Permutation and balance

For \(0<r<w\), the map

\[
T_r(x)=x\mathbin{\mathtt{xor}}(x\mathbin{\mathtt{shr}}r)
\]

is invertible. Its highest \(r\) output bits equal its highest \(r\) input
bits. Successive groups of \(r\) lower input bits are then recovered from
already recovered higher bits. Equivalently,

\[
T_r^{-1}(y)
=y\mathbin{\mathtt{xor}}(y\mathbin{\mathtt{shr}}r)
\mathbin{\mathtt{xor}}(y\mathbin{\mathtt{shr}}2r)
\mathbin{\mathtt{xor}}\cdots
\]

with shifts below \(w\).

Addition by \(b\) is a permutation modulo \(2^w\). Multiplication by an odd
integer is also a permutation because every odd integer is a unit modulo
\(2^w\). Each stage defining \(P\) is therefore bijective, so

\[
\boxed{P\text{ is a permutation}.}
\]

Now write \(Q=qN+r\), \(0\le r<N\). Bucket \(j\) of \(R_N\) is the set of
integers satisfying

\[
\frac{jQ}{N}\le x<\frac{(j+1)Q}{N}.
\]

Its integer cardinality is

\[
\left\lceil\frac{(j+1)Q}{N}\right\rceil
-
\left\lceil\frac{jQ}{N}\right\rceil,
\]

which is either \(q\) or \(q+1\). Summing all bucket sizes gives
\(qN+r\), so exactly \(r\) buckets have size \(q+1\).

Translation by \(s\) and \(P\) are permutations. They merely permute the
domain before \(R_N\), so every \(H_{N,s}\) has the same preimage multiset.

For any map from \(Q\) points to \(N\) buckets, if all bucket sizes differed
by less than one they would be equal. When \(N\nmid Q\), equality is
impossible, so maximum-minus-minimum is at least one. When \(N\mid Q\), the
minimum is zero. The sizes \(q,q+1\) attain these respective lower bounds.
Thus range reduction is optimally balanced.

## C. Exact collision law

Let the bucket preimage sizes be \(n_j\). Independence and uniformity give

\[
\Pr[H(X)=H(Y)]
=\sum_j(n_j/Q)^2.
\]

Substituting \(r\) sizes \(q+1\) and \(N-r\) sizes \(q\),

\[
\Pr[H(X)=H(Y)]
=\frac{r(q+1)^2+(N-r)q^2}{Q^2}.
\]

Because \(Q=qN+r\),

\[
r(q+1)^2+(N-r)q^2
=Nq^2+2rq+r
=\frac{Q^2}{N}+\frac{r(N-r)}{N}.
\]

Hence

\[
\boxed{
\Pr[H(X)=H(Y)]
=\frac1N+\frac{r(N-r)}{NQ^2}.
}
\]

The correction is nonnegative. Also

\[
r(N-r)\le N^2/4,
\]

so

\[
\boxed{
\frac1N\le\Pr[H(X)=H(Y)]
\le\frac1N+\frac{N}{4Q^2}.
}
\]

For \(N_0=2^k\mid Q\), its remainder is zero and

\[
\boxed{C_0=1/N_0.}
\]

For \(N_1=\lfloor4N_0/3\rfloor\), let
\(r_1=Q\bmod N_1\). Then the exact comparison is

\[
\boxed{
C_1-C_0
=
\frac1{N_1}-\frac1{N_0}
+
\frac{r_1(N_1-r_1)}{N_1Q^2}.
}
\]

The first term is negative. A sufficient explicit proof that the whole
expression is negative is

\[
\frac{N_1}{4Q^2}
<
\frac1{N_0}-\frac1{N_1}.
\]

This holds for the intended regime \(N_1\le Q\) except possibly tiny
degenerate word spaces, which the exact displayed formula decides directly.
No step treats two salts as independent; the result is only the marginal law
for each fixed salt.

## D. Deterministic state equivalence

Induct on the coded step \(t\).

At \(t=0\), the arrays, coder states, and all auxiliary states are identical
by hypothesis. Assume equality immediately before step \(t\). Both machines
have the same decoded history and current state, so they form the same keys.
Fixed-width arithmetic, the same salt, the same permutation, and the same
range reduction produce the same index for every key. The selected cells and
their contents are therefore equal.

Identical replacement and prediction rules produce the same replacement
choice and integer probability. The arithmetic coders apply the same integer
transition to the same coder state and the same symbol. Finally, identical
update rules write identical values to identical cells and auxiliary state.
The complete states are equal before step \(t+1\).

By induction, every probability, coder transition, and model state agrees.
During decoding, the common probability partitions the coder interval in the
same way as during encoding, so the same next symbol is recovered. Hash
collisions can affect the probability sequence but cannot affect
losslessness when both sides reproduce them exactly.

## E. Certificate and verifier

A certificate contains:

1. \(w,N,B,M,g,A\) as fixed-width unsigned integers;
2. \(a,b,c,r_1,r_2,r_3\) and every salt;
3. the claimed usable cell count and total allocation;
4. a hash of the exact index routine or its finite instruction encoding;
5. tuples \((x,s,\widehat j)\) for all required test vectors.

The verifier checks:

\[
N=\lfloor M/B\rfloor,\qquad
\text{allocation}=B(N+g)+A,
\]

oddness of \(a,c\), shift bounds, and \(1\le N\le2^w\). It evaluates the
fixed-width routine on each tuple and requires

\[
\widehat j
=
\left\lfloor
\frac{N\,P(x+s\bmod2^w)}{2^w}
\right\rfloor
<N.
\]

For \(T\) test tuples, direct verification performs exactly \(T\)
permutation evaluations, \(T\) full-width products, \(T\) high-word
extractions, and \(T\) equality-and-range checks, plus constant header work.

## Transfer conclusion

With a former budget \(128\cdot2^k\), associativity ten currently uses
\(96\cdot2^k\) indexed bytes. DRB-1 permits

\[
\left\lfloor\frac{128\cdot2^k}{96}\right\rfloor
\]

indexed cells while staying within the former byte budget, apart from
explicitly charged guards and alignment. This recovers almost one third more
cells than the current associativity-ten realization.

The result is constructive and decoder-reproducible. It proves no compression
gain: the new permutation changes collision identities, and only exact native
arithmetic replay can determine whether those changes help the target stream.

