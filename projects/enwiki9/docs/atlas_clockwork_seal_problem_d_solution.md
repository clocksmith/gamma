# Complete Solution to Problem D

## Energy-Ordered Parity Reconstruction

Status: complete mathematical resolution of Problem D under the examination's
solve-or-rigorously-disprove rule. This document does not by itself bind
Seal-2, establish an enwik9 score, or provide runtime eligibility.

The source permits a complete solution of any one problem as an independent
submission. This solution chooses **Problem D: Energy-Ordered Parity
Reconstruction**, using its definitions of \(X=\mathbb F_2^n\), the energy
order, the nested maps \(H_k\), and the decoder \(D_k\).

Two literal qualifications are necessary:

1. D3 is false when "an arbitrary finite \(B\)" includes
   \(B=\varnothing\). The corrected universally valid condition is
   \[
   \ker H\cap(B-B)\subseteq\{0\}.
   \]
   For nonempty \(B\), this is equivalent to the stated equality with
   \(\{0\}\).

2. The D4 count of exactly \(j\) matrix-vector evaluations is correct for the
   specified candidate-by-candidate direct verifier. It is not an
   unconditional lower bound for every possible verifier unless that
   computational model is imposed.

## 0. Assumptions and notation

All vector and matrix arithmetic is over \(\mathbb F_2\). Thus subtraction and
addition coincide:

\[
u-v=u+v.
\]

For \(B\subseteq X\), write

\[
B-B=\{u-v:u,v\in B\}=\{u+v:u,v\in B\}.
\]

Let

\[
K_k=\ker H_k.
\]

Because the rows are nested, \(H_k\) consists of the first \(k\) rows of
\(H_n\). Since \(H_n\) has rank \(n\), its rows are linearly independent, so
every prefix of \(k\) rows is independent. Therefore

\[
\operatorname{rank}H_k=k.
\]

Consequently, every \(H_k:X\to\mathbb F_2^k\) is surjective, each syndrome
class is nonempty, and \(D_k(s)\) is well-defined because \(\prec_E\) is a
total order on the finite set \(X\).

For fixed \(x\), define

\[
P_x=\{y\in X:y\prec_E x\},
\qquad
S_x=\{y+x:y\prec_E x\}.
\]

Translation by \(x\) is a bijection, hence

\[
|S_x|=|P_x|=r_E(x)-1.
\]

Also \(0\notin S_x\), since \(y+x=0\) would imply \(y=x\), contradicting
\(y\prec_E x\).

## D1. Exact collision characterization

### Theorem D1

For every \(k\),

\[
D_k(H_kx)=x
\quad\Longleftrightarrow\quad
K_k\cap S_x=\varnothing.
\]

### Proof

The set of vectors with the same syndrome as \(x\) is exactly its coset modulo
\(K_k\):

\[
\begin{aligned}
H_k(y)=H_k(x)
&\Longleftrightarrow H_k(y)+H_k(x)=0\\
&\Longleftrightarrow H_k(y+x)=0\\
&\Longleftrightarrow y+x\in K_k.
\end{aligned}
\]

Thus

\[
\{y:H_k(y)=H_k(x)\}=x+K_k.
\]

By definition,

\[
D_k(H_kx)=\min_{\prec_E}(x+K_k).
\]

Therefore \(D_k(H_kx)=x\) exactly when no element of \(x+K_k\) precedes
\(x\). Such an earlier element exists precisely when there is a \(y\prec_E x\)
satisfying

\[
y+x\in K_k.
\]

But the residuals \(y+x\) for \(y\prec_E x\) are exactly the members of
\(S_x\). Hence an earlier collision exists exactly when

\[
K_k\cap S_x\ne\varnothing.
\]

Negating this condition proves the equivalence. \(\square\)

### Minimum successful depth

Define

\[
k_*(x)=\min\{k\in\{0,\ldots,n\}:D_k(H_kx)=x\}.
\]

By the theorem,

\[
\boxed{
k_*(x)=
\min\{k:\ker H_k\cap S_x=\varnothing\}.
}
\]

This minimum always exists. Indeed, \(H_n\) has rank \(n\), so

\[
K_n=\{0\},
\]

while \(0\notin S_x\). Thus \(K_n\cap S_x=\varnothing\).

Moreover, because the maps are nested,

\[
K_{k+1}\subseteq K_k.
\]

Therefore, once reconstruction succeeds at some depth \(k\), it succeeds at
every later depth.

## D2. Finite separating maps

Let \(S=S_x\). Recall that \(S\subseteq X\setminus\{0\}\).

### Probabilistic existence theorem

#### Theorem

If

\[
2^k>|S|,
\]

then there exists a linear map

\[
H:\mathbb F_2^n\to\mathbb F_2^k
\]

such that

\[
\ker H\cap S=\varnothing.
\]

#### Proof

Choose a random \(k\times n\) binary matrix \(H\), with all \(kn\) entries
independent and uniform in \(\mathbb F_2\).

Fix \(v\ne0\). For one random row \(h\), the dot product \(h\cdot v\) is
uniformly distributed in \(\mathbb F_2\). To see this directly, choose a
coordinate \(a\) with \(v_a=1\). Once all entries of \(h\) except \(h_a\) are
fixed, exactly one of the two values of \(h_a\) makes \(h\cdot v=0\). Hence

\[
\Pr[h\cdot v=0]=\frac12.
\]

The \(k\) rows are independent, so

\[
\Pr[Hv=0]=2^{-k}.
\]

Using the union bound,

\[
\begin{aligned}
\Pr[\ker H\cap S\ne\varnothing]
&=\Pr[\exists v\in S:Hv=0]\\
&\le\sum_{v\in S}\Pr[Hv=0]\\
&=|S|2^{-k}\\
&<1.
\end{aligned}
\]

Thus the probability of avoiding every member of \(S\) is positive. Therefore
at least one such matrix exists. \(\square\)

This argument also covers \(k=0\): the hypothesis \(1>|S|\) then forces
\(S=\varnothing\), and the zero-row map succeeds.

### Depth bound in terms of energy rank

Since

\[
|S_x|=r_E(x)-1,
\]

take

\[
k_0=\left\lceil\log_2 r_E(x)\right\rceil.
\]

Then

\[
2^{k_0}\ge r_E(x)>r_E(x)-1=|S_x|.
\]

Therefore a separating map exists with \(k=k_0\).

Also \(r_E(x)\le |X|=2^n\), so

\[
k_0=\left\lceil\log_2r_E(x)\right\rceil\le n.
\]

We have proved the stronger bound

\[
\boxed{
k\le \left\lceil\log_2r_E(x)\right\rceil\le n.
}
\]

In particular, the requested weaker statement follows:

\[
\boxed{
k\le
\min\left\{
n,
\left\lceil\log_2r_E(x)\right\rceil+1
\right\}.
}
\]

For the resulting map \(H\), define the corresponding energy-minimum decoder

\[
D_H(s)=\min_{\prec_E}\{y:H(y)=s\}.
\]

Because \(\ker H\cap S_x=\varnothing\), the proof of D1 applies verbatim and
gives

\[
D_H(Hx)=x.
\]

### Deterministic finite construction

Fix a row-major lexicographic ordering of all \(k\times n\) binary matrices.
There are exactly

\[
2^{kn}
\]

such matrices.

For each matrix \(M\) in that order, perform the finite test

\[
Mv\ne0
\qquad\text{for every }v\in S_x.
\]

The probabilistic proof establishes that at least one matrix passes. Therefore
the lexicographically first passing matrix is well-defined and gives a
deterministic finite construction.

No efficiency claim is needed: the examination asks for a finite construction,
and exhaustive finite search supplies one.

### Deleting dependent rows

Let \(M\) be a successful matrix. Scan its rows in their original order,
retaining a row exactly when it is not in the span of the rows already
retained. Let the retained rows be

\[
g_1,\ldots,g_r.
\]

They are linearly independent and span the same row space as all rows of
\(M\). Let \(M'\) be the \(r\times n\) matrix with these rows.

For any \(v\),

\[
Mv=0
\]

means that every row of \(M\) has zero dot product with \(v\). Since every row
of \(M\) is a linear combination of \(g_1,\ldots,g_r\), this is equivalent to

\[
g_i\cdot v=0\quad(1\le i\le r),
\]

which is equivalent to

\[
M'v=0.
\]

Hence

\[
\ker M'=\ker M.
\]

Therefore \(M'\) remains successful:

\[
\ker M'\cap S_x=\varnothing.
\]

### Extension to a nested full-rank family

The independent linear functionals \(g_1,\ldots,g_r\) can be extended to a
basis

\[
g_1,\ldots,g_r,g_{r+1},\ldots,g_n
\]

of the dual space \((\mathbb F_2^n)^*\). Explicitly, repeatedly choose the
lexicographically first row vector outside the span of the rows already
selected. Because the span has dimension less than \(n\) until completion,
such a vector always exists.

For each \(t\in\{0,\ldots,n\}\), define \(H_t\) to have rows

\[
g_1,\ldots,g_t.
\]

Then:

- \(H_0\) is the zero-row map.
- The first \(t\) rows of \(H_{t+1}\) are \(H_t\).
- \(H_n\) has rank \(n\).
- \(H_r=M'\), so
  \[
  \ker H_r\cap S_x=\varnothing.
  \]

Thus the constructed separating map is embedded at depth \(r\) in a nested
full-rank family.

## D3. Structured residual sets

The prompt states the theorem for "an arbitrary finite \(B\)" with equality

\[
\ker H\cap(B-B)=\{0\}.
\]

As written, this has one empty-set counterexample.

### Literal counterexample

Let

\[
B=\varnothing.
\]

Every coset of \(\ker H\) meets \(B\) in zero points, so every coset certainly
meets \(B\) in at most one point.

But

\[
B-B=\varnothing,
\]

and therefore

\[
\ker H\cap(B-B)=\varnothing\ne\{0\}.
\]

Thus the stated equivalence is false for empty \(B\).

The universally correct formulation is

\[
\boxed{
\text{Every coset of }\ker H\text{ meets }B\text{ at most once}
\iff
\ker H\cap(B-B)\subseteq\{0\}.
}
\]

When \(B\ne\varnothing\), we have \(0=b-b\in B-B\), and of course
\(0\in\ker H\). Therefore the intersection contains \(0\), and the subset
condition becomes exactly

\[
\ker H\cap(B-B)=\{0\}.
\]

### Corrected difference-set theorem

Let \(K=\ker H\).

#### Forward direction

Assume every coset of \(K\) meets \(B\) in at most one point.

Take

\[
z\in K\cap(B-B).
\]

Then \(z=u-v\) for some \(u,v\in B\). Since \(z\in K\),

\[
u-v\in K,
\]

so \(u\) and \(v\) lie in the same coset of \(K\). By the assumed uniqueness
within every coset,

\[
u=v.
\]

Hence \(z=u-v=0\). Therefore

\[
K\cap(B-B)\subseteq\{0\}.
\]

#### Reverse direction

Assume

\[
K\cap(B-B)\subseteq\{0\}.
\]

Suppose \(u,v\in B\) lie in the same coset of \(K\). Then

\[
u-v\in K.
\]

Since \(u,v\in B\), we also have

\[
u-v\in B-B.
\]

Thus

\[
u-v\in K\cap(B-B)\subseteq\{0\},
\]

so \(u-v=0\), and hence \(u=v\). Therefore no coset contains two distinct
members of \(B\). \(\square\)

### Application to Hamming balls

Assume

\[
B_r=\{x\in\mathbb F_2^n:\operatorname{wt}(x)\le r\},
\qquad 0\le r\le n,
\]

where \(\operatorname{wt}\) is Hamming weight.

#### Lemma

\[
\boxed{
B_r-B_r=B_{\min(2r,n)}.
}
\]

#### Proof

Because subtraction equals addition, take \(u,v\in B_r\). Then

\[
\operatorname{wt}(u+v)
\le
\operatorname{wt}(u)+\operatorname{wt}(v)
\le 2r.
\]

Every vector has weight at most \(n\), so

\[
u+v\in B_{\min(2r,n)}.
\]

This proves

\[
B_r-B_r\subseteq B_{\min(2r,n)}.
\]

Conversely, let \(z\in B_{\min(2r,n)}\), and put
\(t=\operatorname{wt}(z)\). Thus \(t\le2r\). Partition the support of \(z\)
into two disjoint sets \(P,Q\), each of size at most \(r\). Such a partition
exists because the total support size is at most \(2r\).

Let \(u\) and \(v\) be the indicator vectors of \(P\) and \(Q\). Then

\[
u,v\in B_r
\]

and, because \(P,Q\) are disjoint and their union is the support of \(z\),

\[
u+v=z.
\]

Thus \(z\in B_r-B_r\), proving the reverse inclusion. \(\square\)

### Minimum-distance characterization

Let

\[
K=\ker H.
\]

Regard \(K\) as a binary linear code and define

\[
d_{\min}(K)
=
\min\{\operatorname{wt}(z):z\in K,\ z\ne0\},
\]

with

\[
d_{\min}(\{0\})=\infty.
\]

By the corrected difference-set theorem, every coset meets \(B_r\) at most
once exactly when

\[
K\cap B_{\min(2r,n)}=\{0\}.
\]

We claim this is equivalent to

\[
\boxed{d_{\min}(K)>2r.}
\]

If \(2r\le n\), the equivalence is immediate: avoiding all nonzero vectors of
weight at most \(2r\) means precisely that the least nonzero codeword weight
exceeds \(2r\).

If \(2r>n\), then

\[
B_{\min(2r,n)}=B_n=X.
\]

Thus uniqueness is possible exactly when \(K=\{0\}\). Under the stated
convention, this is equivalent to

\[
d_{\min}(K)=\infty>2r.
\]

Any nonzero binary code has minimum distance at most \(n<2r\), so no other
kernel succeeds.

Therefore, in all cases,

\[
\boxed{
\text{Every coset meets }B_r\text{ at most once}
\iff
d_{\min}(\ker H)>2r.
}
\]

### Syndrome-counting bound

Under the uniqueness condition, the restriction

\[
H|_{B_r}:B_r\to\mathbb F_2^k
\]

is injective. Indeed, if \(H(u)=H(v)\), then \(u\) and \(v\) lie in the same
kernel coset, so uniqueness gives \(u=v\).

Therefore

\[
|B_r|
\le
|\mathbb F_2^k|
=
2^k.
\]

Hence

\[
\boxed{2^k\ge |B_r|.}
\]

For \(0\le r\le n\),

\[
|B_r|=\sum_{t=0}^{r}\binom nt,
\]

so equivalently

\[
k\ge
\left\lceil
\log_2\left(\sum_{t=0}^{r}\binom nt\right)
\right\rceil.
\]

### Union of translated Hamming balls

Let

\[
B=\bigcup_{i=1}^{m}(p_i+B_{r_i}),
\qquad m\ge1.
\]

We first prove the unequal-radius version of the preceding lemma:

\[
\boxed{
B_r+B_s=B_{\min(r+s,n)}.
}
\]

The forward inclusion follows from

\[
\operatorname{wt}(u+v)
\le\operatorname{wt}(u)+\operatorname{wt}(v)
\le r+s.
\]

For the reverse inclusion, take \(z\) of weight \(t\le r+s\). Partition its
support into \(P,Q\) with

\[
|P|\le r,\qquad |Q|\le s.
\]

For example, assign \(\min(r,t)\) support coordinates to \(P\) and the rest to
\(Q\); the remaining number is at most \(s\). The corresponding indicator
vectors \(u,v\) satisfy \(z=u+v\).

Now, for each ordered pair \(i,j\),

\[
\begin{aligned}
(p_i+B_{r_i})-(p_j+B_{r_j})
&=
p_i+p_j+(B_{r_i}+B_{r_j})\\
&=
p_i+p_j+B_{\min(r_i+r_j,n)}.
\end{aligned}
\]

Therefore

\[
\boxed{
B-B
=
\bigcup_{i,j=1}^{m}
\left(
p_i+p_j+B_{\min(r_i+r_j,n)}
\right).
}
\]

Applying the corrected difference-set theorem, every coset of
\(K=\ker H\) meets \(B\) in at most one point if and only if

\[
K\cap(B-B)\subseteq\{0\}.
\]

Using the displayed union, this is equivalent to the exact pairwise condition

\[
\boxed{
K\cap
\left(
p_i+p_j+B_{\min(r_i+r_j,n)}
\right)
\subseteq\{0\}
\quad
\text{for every }i,j.
}
\]

Equivalently, in nonzero-kernel-vector form,

\[
\boxed{
\operatorname{wt}(z+p_i+p_j)
>
\min(r_i+r_j,n)
}
\]

for every \(z\in K\setminus\{0\}\) and every \(i,j\).

When \(r_i+r_j\ge n\), the right-hand ball is all of \(X\); consequently that
pair forces \(K=\{0\}\).

## D4. Bounded-search first-hit certificate

The proposed verifier receives \(H,s,S_B\), and a claimed pair \((j,x)\), and
the problem asks for exact first-hit conditions and a \(j\)-evaluation
direct-verification count.

Assume

\[
1\le j\le B\le 2^n.
\]

Because \(\prec_E\) is a total order, the candidates

\[
S_B=(y_1,\ldots,y_B)
\]

are distinct.

### First-hit theorem

The pair \((j,x)\) is a valid certificate that the bounded decoder returns
\(x\) if and only if

\[
\boxed{
x=y_j,\qquad H(x)=s,\qquad H(y_i)\ne s\quad(1\le i<j).
}
\]

#### Necessity

Suppose the bounded decoder returns \(x\), with claimed first-hit index \(j\).

The decoder returns only candidates in its ordered list, so

\[
x=y_j.
\]

It returns a candidate only when its syndrome is \(s\), hence

\[
H(x)=s.
\]

Finally, \(j\) is the first matching index. Therefore no earlier candidate
matches:

\[
H(y_i)\ne s
\qquad(1\le i<j).
\]

All three conditions are necessary.

#### Sufficiency

Conversely, suppose

\[
x=y_j,\qquad H(x)=s,
\]

and all earlier candidates have syndromes unequal to \(s\).

The bounded decoder examines \(y_1,\ldots,y_B\) in order. For indices \(i<j\),
it does not return because \(H(y_i)\ne s\). At index \(j\),

\[
H(y_j)=H(x)=s,
\]

so it returns \(y_j=x\).

Thus the stated checks are sufficient. \(\square\)

### Direct-verification cost

The natural direct verifier performs:

1. The equality check \(x=y_j\).
2. One evaluation \(H(y_i)\) for every \(i<j\).
3. One evaluation \(H(y_j)=H(x)\).

The equality and index checks require no matrix-vector evaluation. The
syndrome checks require

\[
(j-1)+1=j
\]

matrix-vector evaluations.

A valid certificate whose first match occurs at \(j\) forces this direct scan
to reach the \(j\)-th candidate. Therefore:

\[
\boxed{
\text{The candidate-by-candidate direct verifier uses exactly }j
\text{ matrix-vector evaluations in its worst case.}
}
\]

### Qualification: \(j\) is not a universal lower bound

If "requires exactly \(j\)" is interpreted as saying that every possible
verifier must perform \(j\) separate matrix-vector evaluations, the claim is
false without an additional computational-model restriction.

Let

\[
W=\operatorname{span}\{y_1,\ldots,y_j\}
\]

and let \(w_1,\ldots,w_r\) be a basis of \(W\). Then

\[
r\le n.
\]

Evaluate \(H\) only on the basis vectors:

\[
H(w_1),\ldots,H(w_r).
\]

Every \(y_i\) has a known representation

\[
y_i=\sum_{\ell=1}^{r}\alpha_{i\ell}w_\ell,
\]

so linearity gives

\[
H(y_i)
=
\sum_{\ell=1}^{r}\alpha_{i\ell}H(w_\ell).
\]

Thus all \(j\) candidate syndromes can be derived from only \(r\le n\)
matrix-vector evaluations. In particular, whenever \(j>n\),

\[
r\le n<j.
\]

So no unrestricted lower bound of \(j\) evaluations is possible.

An explicit valid instance is obtained by taking \(n\ge2\), \(j=n+1\),
\(H=I_n\), \(s=y_j\), and \(x=y_j\). Since the candidates are distinct,

\[
H(y_i)=y_i\ne y_j=s
\quad(i<j),
\]

so the certificate is valid. Yet the identity form of \(H\) makes all
syndrome values immediately known without performing \(j\) general
matrix-vector products.

Therefore the rigorous conclusion is:

\[
\boxed{
\begin{array}{l}
\text{Exactly }j\text{ evaluations for the specified direct scan;}\\[2mm]
\text{not an information-theoretic lower bound for arbitrary verifiers.}
\end{array}
}
\]

## Final conclusions

For Problem D:

\[
D_k(H_kx)=x
\iff
\ker H_k\cap S_x=\varnothing,
\]

and the first successful nested depth is exactly the first depth whose kernel
avoids \(S_x\).

A separating linear map exists whenever

\[
2^k>|S_x|,
\]

by both a random-matrix union-bound proof and a finite lexicographic
construction. In fact,

\[
k\le\left\lceil\log_2r_E(x)\right\rceil
\]

suffices, which is stronger than the requested estimate. Dependent rows can be
removed without changing the kernel, and the remaining rows extend to a nested
full-rank family.

For arbitrary \(B\), the universally correct uniqueness criterion is

\[
\ker H\cap(B-B)\subseteq\{0\}.
\]

The prompt's equality formulation requires \(B\ne\varnothing\). For Hamming
balls, uniqueness is equivalent to

\[
d_{\min}(\ker H)>2r
\]

and implies

\[
2^k\ge|B_r|.
\]

For unions of translated balls, the exact condition is

\[
\ker H\cap
\left(
p_i+p_j+B_{\min(r_i+r_j,n)}
\right)
\subseteq\{0\}
\]

for every pair \(i,j\).

Finally, the three stated first-hit checks are necessary and sufficient. The
direct sequential verifier uses exactly \(j\) syndrome evaluations, although
\(j\) is not a universal lower bound once linear reuse or other verification
strategies are permitted.

## Research interpretation

This solution validates the algebraic foundation of energy-ordered parity
reconstruction. It does not construct a low-rank enwik9 energy, an efficient
bounded decoder, an under-target codec, or an eligible full-corpus execution.
The remaining constructive problem is to produce a cheaply searchable energy
ordering that gives real WRT blocks sufficiently low rank.
