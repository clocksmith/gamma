# Internal Solution Attempt for ACS-MATH-DRAFT-3-WORKING

Status: `COMPLETE INTERNAL CONSTRUCTIVE ATTEMPT`

This manuscript was produced during development of Draft 3. It is not an
independent solver submission, examination receipt, priority claim, or Seal
artifact.

All logarithms are base two.

---

# Solution to Problem A

## A.1 Row assignments and relaxed duality

For \(z\in\{1,\ldots,K\}^J\), define

\[
F_z(q)=
\sum_jg_{j,z_j}+\sum_kn_k(z)\log q_k,
\]

where a positive count paired with \(q_k=0\) gives \(-\infty\), and a
zero-count term is zero. Rowwise independence gives

\[
\mathcal V_G(q)=\max_zF_z(q).
\]

Fix \(z\), write \(n_k=n_k(z)\), and let \(S=\{k:n_k>0\}\). Put
\(p_k=n_k/J\). For any \(q\) finite on \(S\), set

\[
Q=\sum_{k\in S}q_k,\qquad r_k=q_k/Q.
\]

Then

\[
\sum_{k\in S}n_k\log q_k
=J\log Q+J\sum_{k\in S}p_k\log r_k.
\]

Since \(Q\le1\), the first term is at most zero. Gibbs' inequality gives

\[
\sum_{k\in S}p_k\log r_k
\le
\sum_{k\in S}p_k\log p_k.
\]

Equality in both inequalities holds exactly when

\[
Q=1,\qquad r_k=p_k.
\]

The positive coordinates then already sum to one, so every unused coordinate
is zero. Thus the unique maximizer for fixed \(z\) is

\[
q_k=\frac{n_k(z)}J
\]

for every \(k\), and its value is

\[
\sum_jg_{j,z_j}
+\sum_{k:n_k(z)>0}n_k(z)\log\frac{n_k(z)}J.
\]

There are finitely many assignments. Therefore

\[
\begin{aligned}
\max_q\mathcal V_G(q)
&=\max_q\max_zF_z(q)\\
&=\max_z\max_qF_z(q)\\
&=
\max_z\left[
\sum_jg_{j,z_j}
+\sum_{k:n_k(z)>0}n_k(z)\log\frac{n_k(z)}J
\right].
\end{aligned}
\]

This also proves existence.

Suppose \(q\) is optimal and choose any rowwise maximizing assignment \(z\) at
\(q\). Then \(F_z(q)\) is the common optimum. Since the maximum of \(F_z\)
cannot exceed that common optimum, \(q\) maximizes \(F_z\). The fixed-assignment
calculation forces \(q_k=n_k(z)/J\), and \(z\) is dual-optimal.

Conversely, if \(z\) is dual-optimal and \(q_k=n_k(z)/J\), then
\(F_z(q)\) equals the dual optimum. Hence \(\mathcal V_G(q)\) equals it as
well. If \(z\) were not rowwise maximizing, \(\mathcal V_G(q)\) would be
strictly larger, a contradiction.

Consequently every rowwise maximizing assignment at an optimal \(q\) has the
same count vector \(Jq\). In particular,

\[
q_k=0\iff n_k(z)=0.
\]

Ties may change which rows receive a label, but not the value or the count
vector associated with an optimal \(q\).

## A.2 Integer prefix penalty

For a legal integer length vector, set \(q_k=2^{-\ell_k}\). Kraft's inequality
puts \(q\) in \(\Delta_K\), and

\[
V_G(\ell)=\mathcal V_G(q)\le\mathcal V^*(G).
\]

Thus \(V^*(G)\le\mathcal V^*(G)\).

Let \(q^*\) be relaxed-optimal. Set

\[
\ell_k=
\begin{cases}
\lceil-\log q_k^*\rceil,&q_k^*>0,\\
\infty,&q_k^*=0.
\end{cases}
\]

Then \(2^{-\ell_k}\le q_k^*\), so Kraft holds. For positive coordinates,

\[
-\ell_k\ge\log q_k^*-1.
\]

Therefore every row loses at most one bit:

\[
\max_k(g_{jk}-\ell_k)
\ge
\max_k(g_{jk}+\log q_k^*)-1.
\]

Summing proves

\[
\mathcal V^*(G)-J\le V^*(G)\le\mathcal V^*(G).
\]

To construct actual words, sort active indices by nondecreasing length, with
the fixed index order breaking ties. For lengths \(L_1,\ldots,L_r\), set

\[
C_1=0,\qquad
C_i=(C_{i-1}+1)2^{L_i-L_{i-1}}.
\]

Assign the \(L_i\)-bit representation of \(C_i\). Kraft's inequality implies
\(C_i<2^{L_i}\), and the associated dyadic intervals are disjoint, hence the
words are prefix-free. If one length is zero, Kraft forces it to be the only
active word.

### Asymptotic sharpness

For \(J\ge2\), take \(K=2\). Choose \(M>J\). For rows
\(1,\ldots,J-1\), set

\[
g_{j1}=0,\qquad g_{j2}=-M,
\]

and for row \(J\), set

\[
g_{J1}=-M,\qquad g_{J2}=0.
\]

The intended assignment has counts \((J-1,1)\), gain zero, and dual value

\[
-JH_2(1/J),
\]

where \(H_2\) is binary entropy. Every other assignment incurs at least one
\(-M\) mismatch and has entropy term at most zero, so its dual value is at most
\(-M<-JH_2(1/J)\). Thus

\[
\mathcal V^*(G)=-JH_2(1/J).
\]

In an integer binary prefix code with both symbols active, both lengths are at
least one. Each row then contributes at most \(-1\), while lengths
\((1,1)\) attain total \(-J\). Inactivating either symbol incurs a mismatch
penalty worse than \(-J\). Hence

\[
V^*(G)=-J.
\]

The gap ratio is

\[
\frac{\mathcal V^*(G)-V^*(G)}J
=1-H_2(1/J)\longrightarrow1.
\]

Thus no universal replacement of \(J\) by \(cJ\) with \(c<1\) is possible.

## A.3 Exact finite prefix price and Huffman merging

Ignore zero-count symbols and write the positive weights as
\(w_1,\ldots,w_r\).

If \(r=1\), the empty word is feasible and optimal, so \(L(n)=0\).

Assume \(r\ge2\). Any optimal prefix tree may be made full: an internal vertex
with one child can be suppressed, shortening all descendant words. In a full
optimal tree, choose two sibling leaves at maximum depth. By exchanging leaf
labels, assigning smaller weights to greater depths never increases weighted
path length. Hence the two least weights can be placed on a deepest sibling
pair.

Contract that pair into a leaf of weight equal to their sum. If the contracted
tree has external path length \(L'\), expanding the merged leaf increases the
cost by exactly the sum of the two merged weights. Conversely, every tree on
the contracted weights expands to a tree on the original weights with that
same increment. Therefore an optimal tree exists if and only if the contracted
tree is optimal. Induction proves the Huffman rule: repeatedly merge the two
least positive weights.

Use the fixed symbol order to break equal-weight ties. At every merge, place
the child whose current canonical label-set minimum is smaller on the left.
This produces a deterministic optimal tree and therefore canonical lengths and
words. It also proves that the minimum defining \(L(n)\) exists.

For a fixed assignment \(z\),

\[
\max_\ell
\left[
\sum_j(g_{j,z_j}-\ell_{z_j})
-\sum_{k:n_k(z)>0}d_k
\right]
=
\sum_jg_{j,z_j}
-L(n(z))
-\sum_{k:n_k(z)>0}d_k.
\]

Taking the maximum over the finite assignment set proves the exact threshold
equivalence in A.4.

## A.4 Stability

For every legal \(\ell\) and row \(j\),

\[
\left|
\max_k(g_{jk}-\ell_k)
-\max_k(g'_{jk}-\ell_k)
\right|\le\varepsilon.
\]

Thus

\[
|V_G(\ell)-V_{G'}(\ell)|\le J\varepsilon.
\]

Taking suprema in both directions gives

\[
|V^*(G)-V^*(G')|\le J\varepsilon.
\]

If \(g'_{jk}=g_{jk}+\varepsilon\) for every entry, then

\[
V^*(G')=V^*(G)+J\varepsilon.
\]

The coefficient \(J\) is therefore exact.

---

# Solution to Problem B

## B.1 Behavioral equivalence

Equality of all prefix-color traces is an equivalence relation. Taking the
empty word shows that equivalent histories have equal current colors. If
\(h\equiv h'\), then for every \(a\in A\) and \(u\in A^*\),

\[
c(T(T(h,a),u))
=c(T(h,au))
=c(T(h',au))
=c(T(T(h',a),u)).
\]

Thus \(T(h,a)\equiv T(h',a)\), so \(\equiv\) is a color-preserving right
congruence.

If \(R\) is any color-preserving right congruence and \(hRh'\), induction on
\(|u|\) gives \(T(h,u)R T(h',u)\). Color preservation then gives equal traces,
so \(h\equiv h'\). Therefore every such \(R\) is contained in \(\equiv\), and
\(\equiv\) is the unique coarsest one.

Let \(N=|Q|\ge2\). On \(Q\), define

\[
q\sim_rq'
\iff
c(T(q,u))=c(T(q',u))
\quad\text{for every }|u|\le r.
\]

If \(\sim_{r+1}=\sim_r\), then \(\sim_r\) is right invariant: equality of all
outputs through depth \(r+1\) implies that equal one-step successors have equal
outputs through depth \(r\). It is also color-preserving. Since \(Q\) is the
behavioral quotient, stabilization can occur only at equality.

The initial color partition has at least two blocks; otherwise the universal
relation would be a nontrivial color-preserving right congruence. Every
nonidentity refinement therefore increases the number of blocks by at least
one. Starting from at least two blocks, equality is reached by depth at most
\(N-2\). Hence every unequal pair has a distinguishing word of length at most
\(N-2\).

For sharpness, take

\[
Q=\{0,\ldots,N-1\},\qquad A=\{a\},
\]

\[
T(i,a)=\min(i+1,N-1),
\]

and color only state \(N-1\) differently. States \(0\) and \(1\) first differ
after \(a^{N-2}\), so the bound is attained.

Choose one representative per quotient class. For each unordered pair, choose
a shortest distinguishing word. The representative list and words form a
finite minimality certificate. Each word has length at most \(N-2\), so the
total listed word length is at most

\[
\binom N2(N-2).
\]

## B.2 Wheeler interval characterization

Assume the order is Wheeler. For \(a<a'\), every target in \(I(a)\) precedes
every target in \(I(a')\), directly by the unequal-label axiom. For fixed
\(a\), the equal-label axiom says \(q\mapsto T(q,a)\) is nondecreasing.

To prove that \(I(a)\) is an interval, let \(x<y<z\) with \(x,z\in I(a)\).
Both endpoints have positive indegree. Since all zero-indegree states come
first, \(y\) also has positive indegree. Let an incoming edge to \(y\) have
label \(b\). If \(b<a\), label ordering forces \(y<x\); if \(b>a\), it forces
\(y>z\). Hence \(b=a\), so \(y\in I(a)\).

Conversely, suppose zero-indegree states come first, one-letter images are
intervals in strict label order, and each letter transition is nondecreasing.
Strict interval order proves the unequal-label Wheeler axiom, and
nondecreasing transitions prove the equal-label axiom. Thus the order is
Wheeler.

We use the following lemma. If \(f\) is nondecreasing on a finite chain,
\(f(Q)\) is an interval, and \(J\subseteq Q\) is an interval, then \(f(J)\) is
an interval. Indeed, any value between \(f(\min J)\) and \(f(\max J)\) occurs
somewhere in \(Q\); monotonicity forces an occurrence inside \(J\).

Now \(I(\epsilon)=Q\). If \(I(w)\) is an interval, then

\[
I(wa)=T_a(I(w))
\]

is an interval by the lemma. Totality and \(Q\ne\varnothing\) make every
\(I(w)\) nonempty.

## B.3 Finite unfolding

Order words colexicographically, equivalently by lexicographic order of their
reversals. Empty-word vertices are exactly the indegree-zero vertices and
occur first.

If \(a<a'\), the reversed target words \(a\,w^{\rm rev}\) and
\(a'\,{w'}^{\rm rev}\) are in strict label order. For equal labels, appending
the same final symbol preserves colexicographic source-word order; if source
words agree, the supplied state order is preserved. Hence the unfolding is
Wheeler.

No vertices are identified, and each vertex explicitly stores its terminal
tag \(T(q,w)\), so unequal tagged behaviors remain distinct.

There are \(|A|^i\) words of length \(i\), with the usual value one for the
empty word. Therefore the vertex count is

\[
|Q|\sum_{i=0}^L|A|^i.
\]

Every vertex below depth \(L\) has \(|A|\) outgoing edges, giving

\[
|Q|\sum_{i=1}^L|A|^i
\]

edges.

For fixed \(u\), the word components in \(J_L(u)\) are exactly the words
ending in \(u\). Their reversals share prefix \(u^{\rm rev}\), so they form a
lexicographic interval. Each word carries one contiguous block of all states,
hence \(J_L(u)\) is one interval.

A finite certificate lists the supplied state order, all vertices in claimed
order, every tag, and every edge. A direct verifier checks the product vertex
set, colex-state ordering, tag equation, complete edge equation, and the three
Wheeler axioms.

## B.4 Continuation multiplicity

An \(N\)-element chain has exactly

\[
\sum_{i=1}^N(N-i+1)=\frac{N(N+1)}2
\]

nonempty intervals. Every continuation image is one of them, so

\[
\left|\{I(w):w\in A^*\}\right|
\le\frac{N(N+1)}2.
\]

The unary sharpness family from B.1 is Wheeler in natural order and satisfies

\[
I(a^t)=\{t,\ldots,N-1\},
\qquad 0\le t\le N-1,
\]

after shifting indices appropriately. These are \(N\) distinct intervals.
The empty-set term used for partial transition systems is absent because the
transition here is total.

---

# Solution to Problem C

Put \(h=2^{-m}\).

## C.1 Invariant bounds and lattice rounding

If \(\|A_a\|_2\le\rho\) and \(\|b_a\|_2\le B\), then

\[
\|s_{t+1}\|_2\le\rho\|s_t\|_2+B.
\]

Iteration gives

\[
\|s_t\|_2
\le
\rho^{t-1}\|s_1\|_2+
\frac{1-\rho^{t-1}}{1-\rho}B.
\]

The same proof gives, for
\(\|\widehat A_a\|_2\le\widehat\rho<1\) and
\(\|\widehat b_a\|_2\le\widehat B\),

\[
\|\widehat s_t\|_2
\le
\widehat\rho^{t-1}\|\widehat s_1\|_2+
\frac{1-\widehat\rho^{t-1}}{1-\widehat\rho}
(\widehat B+\eta_m),
\]

because state rounding is an additive perturbation of norm at most
\(\eta_m\).

Each coordinate rounding error has magnitude at most \(h/2\). Hence

\[
\|R_m(v)-v\|_2\le\sqrt d\,h/2=\eta_m.
\]

## C.2 Uniform shadowing

Let

\[
\widetilde s_{t+1}
=\widehat A_{a_t}\widehat s_t+\widehat b_{a_t}.
\]

Adding and subtracting suitable terms gives

\[
\begin{aligned}
s_{t+1}-\widehat s_{t+1}
={}&A_{a_t}(s_t-\widehat s_t)
+(A_{a_t}-\widehat A_{a_t})\widehat s_t\\
&+(b_{a_t}-\widehat b_{a_t})
+(\widetilde s_{t+1}-R_m(\widetilde s_{t+1})).
\end{aligned}
\]

Therefore

\[
e_{t+1}
\le
\rho e_t+\varepsilon_AS+\varepsilon_b+\eta_m.
\]

Writing

\[
\delta=\varepsilon_AS+\varepsilon_b+\eta_m,
\]

iteration gives

\[
e_t\le
\rho^{t-1}e_1+
\frac{1-\rho^{t-1}}{1-\rho}\delta.
\]

### Exact compatible scalar construction

Take \(d=1\), \(\rho=\tfrac12\), and choose the tie rule that rounds positive
half-grid points upward. Let

\[
A=\widehat A=\tfrac12,\qquad
\widehat b=0,\qquad b=-\beta,
\]

where \(\beta\ge0\) is rational. Initialize

\[
\widehat s_1=h,\qquad s_1=h-e_1.
\]

Since \(R_m(h/2)=h\), the approximate state remains \(h\). Put
\(d_t=\widehat s_t-s_t\). Then

\[
d_{t+1}
=h-\left[\tfrac12(h-d_t)-\beta\right]
=\tfrac12d_t+\beta+h/2.
\]

Here \(\varepsilon_A=0\), \(\varepsilon_b=\beta\), and \(\eta_m=h/2\).
Choosing nonnegative data makes \(e_t=d_t\), so equality holds in the complete
shadowing formula. A finite \(S\) exists because both scalar recurrences are
bounded.

### Supremal sharpness for arbitrary \(\rho\)

For \(\rho>0\), choose rational \(r\uparrow\rho\).

To approach the initial-error coefficient, take

\[
A=\widehat A=r,\qquad b=\widehat b=0,\qquad
\widehat s_1=0,\qquad s_1=e_1.
\]

The approximate state stays exactly zero and

\[
e_t=r^{t-1}e_1.
\]

Letting \(r\uparrow\rho\), while taking \(m\) large enough that the unrelated
rounding allowance is negligible, approaches \(\rho^{t-1}\).

To approach the accumulated coefficient, take equal coefficient \(r\), zero
initial error, \(\widehat b=0\), and \(b=\beta\). Then

\[
e_t=\beta\sum_{i=0}^{t-2}r^i.
\]

Let \(r\uparrow\rho\) and make \(\beta/\eta_m\) arbitrarily large. The ratio to
the admitted one-step perturbation approaches

\[
\sum_{i=0}^{t-2}\rho^i
=\frac{1-\rho^{t-1}}{1-\rho}.
\]

For \(\rho=0\), take \(r=0\); the coefficients are directly attained. Thus the
displayed coefficients are universal sharp suprema, without claiming exact
lattice compatibility for every rational \(\rho\).

## C.3 Logistic loss transfer

Differentiation gives

\[
\frac{\partial\lambda}{\partial y}
=\frac{\sigma(y)-x}{\ln2},
\qquad
\sigma(y)=\frac{e^y}{1+e^y}.
\]

Its absolute value is at most \(1/\ln2\). For \(x=0\), it approaches that value
as \(y\to+\infty\); for \(x=1\), it approaches it as \(y\to-\infty\). Hence the
constant is sharp.

Moreover,

\[
\begin{aligned}
|\widehat y_t-y_t|
&\le
|(\widehat c-c)^T\widehat s_t|
+|c^T(\widehat s_t-s_t)|
+|\widehat\gamma_{a_t}-\gamma_{a_t}|\\
&\le
\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma.
\end{aligned}
\]

The Lipschitz theorem gives

\[
\sum_{t=1}^n
[\lambda(x_t,\widehat y_t)-\lambda(x_t,y_t)]
\le
\frac1{\ln2}
\sum_{t=1}^n
(\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma).
\]

Using C.2,

\[
\sum_{t=1}^ne_t
\le
e_1\frac{1-\rho^n}{1-\rho}
+
\frac{\delta}{1-\rho}
\left[
n-\frac{1-\rho^n}{1-\rho}
\right].
\]

Thus the closed bound is

\[
\begin{aligned}
\frac1{\ln2}\Bigg[
&n(\varepsilon_cS+\varepsilon_\gamma)
+\|c\|_2e_1\frac{1-\rho^n}{1-\rho}\\
&+\frac{\|c\|_2\delta}{1-\rho}
\left(
n-\frac{1-\rho^n}{1-\rho}
\right)
\Bigg].
\end{aligned}
\]

## C.4 Householder realization

Entrywise nearest rounding of a \(d\times d\) matrix has Frobenius error at
most

\[
\sqrt{d^2(h/2)^2}=dh/2.
\]

The spectral norm is no larger, proving

\[
\|Q_m(M)-M\|_2\le dh/2.
\]

Put

\[
P=\prod_{j=1}^kH_j,\qquad
\widehat P=\prod_{j=1}^k\widehat H_j.
\]

Every \(H_j\) is orthogonal, while
\(\|\widehat H_j\|_2\le1+\varepsilon_H\). The telescoping product identity
gives

\[
\|\widehat P-P\|_2
\le
\sum_{i=1}^k(1+\varepsilon_H)^{i-1}\varepsilon_H
=(1+\varepsilon_H)^k-1.
\]

Therefore

\[
\begin{aligned}
\|\widehat D\widehat P+\widehat E-(DP+E)\|_2
\le{}&
\varepsilon_D(1+\varepsilon_H)^k\\
&+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E.
\end{aligned}
\]

Adding final matrix rounding proves

\[
\|\widehat A-A\|_2
\le
\varepsilon_D(1+\varepsilon_H)^k
+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E+dh/2.
\]

### Rational orthogonal factorization

Let \(Q\in O_d(\mathbb Q)\). Induct on \(d\). If \(Qe_1=e_1\), then \(Q\)
restricts to a rational orthogonal map on \(e_1^\perp\), so induction uses at
most \(d-1\) rational reflections.

Otherwise set

\[
v=Qe_1-e_1\in\mathbb Q^d\setminus\{0\}.
\]

For

\[
H_v=I-2\frac{vv^T}{v^Tv},
\]

orthogonality gives

\[
v^TQe_1=1-e_1^TQe_1,\qquad
v^Tv=2(1-e_1^TQe_1),
\]

and hence \(H_vQe_1=e_1\). The matrix \(H_vQ\) uses at most \(d-1\)
reflections by induction, and \(Q=H_v(H_vQ)\). Thus at most \(d\) rational
Householder reflections suffice.

## C.5 Explicit finite precision

Assume all stored values are nearest-\(m\)-dyadic approximations. Then

\[
\varepsilon_D\le h/2,\qquad
\varepsilon_H\le dh/2,\qquad
\varepsilon_E\le dh/2,
\]

\[
\varepsilon_b,\varepsilon_c,e_1\le\sqrt d\,h/2,
\qquad
\varepsilon_\gamma\le h/2.
\]

The matrix bound becomes

\[
\delta_A(h)
\le
\frac h2(1+dh/2)^k
+d_0[(1+dh/2)^k-1]
+dh.
\]

Impose \(kdh/2\le1\). Then

\[
(1+dh/2)^k\le e,\qquad
(1+dh/2)^k-1\le ekdh/2.
\]

Hence

\[
\delta_A(h)\le C_Ah,\qquad
C_A=d+\frac e2(1+d_0kd).
\]

The one-step state error obeys

\[
\varepsilon_{\rm step}
\le h(SC_A+\sqrt d).
\]

The simpler uniform shadow bound

\[
e_t\le e_1+\frac{\varepsilon_{\rm step}}{1-\rho}
\]

shows that total excess loss is at most

\[
\frac{nh}{\ln2}C_{\rm tot},
\]

where

\[
C_{\rm tot}
=
\frac{S\sqrt d}{2}+\frac12
+\|c\|_2\left[
\frac{\sqrt d}{2}
+\frac{SC_A+\sqrt d}{1-\rho}
\right].
\]

It therefore suffices that

\[
m\ge
\max\left\{
1,\
\left\lceil\log_2^+\frac{kd}{2}\right\rceil,\
\left\lceil
\log_2^+\frac{nC_{\rm tot}}{\varepsilon\ln2}
\right\rceil
\right\},
\]

omitting the middle term when \(k=0\), and writing
\(\log_2^+x=\max(0,\log_2x)\).

### Externally fixed errors

More generally suppose, for \(0<h\le h_0\le1\),

\[
\begin{array}{lll}
\varepsilon_D\le D_0+D_1h,&
\varepsilon_H\le H_0+H_1h,&
\varepsilon_E\le E_0+E_1h,\\
\varepsilon_b\le b_0+b_1h,&
\varepsilon_c\le c_0+c_1h,&
\varepsilon_\gamma\le g_0+g_1h,\\
e_1\le r_0+r_1h.&&
\end{array}
\]

Let \(R_0=1+H_0\), \(R_*=1+H_0+H_1h_0\), and define

\[
\delta_{A,0}
=D_0R_0^k+d_0(R_0^k-1)+E_0,
\]

\[
C_{A,*}
=D_1R_*^k
+(D_0+D_1h_0+d_0)kH_1R_*^{k-1}
+E_1+d/2.
\]

The mean-value theorem gives

\[
\delta_A(h)\le\delta_{A,0}+C_{A,*}h.
\]

Define the \(m\)-independent bracket

\[
F_0
=c_0S+g_0
+\|c\|_2\left[
r_0+\frac{S\delta_{A,0}+b_0}{1-\rho}
\right]
\]

and the linear coefficient

\[
C_*
=c_1S+g_1
+\|c\|_2\left[
r_1+
\frac{SC_{A,*}+b_1+\sqrt d/2}{1-\rho}
\right].
\]

The sufficient loss bracket is at most \(F_0+C_*h\). A finite precision is
guaranteed by this bound exactly when

\[
R:=\frac{\varepsilon\ln2}{n}-F_0>0.
\]

When \(R>0\) and \(C_*>0\), it suffices to choose

\[
2^{-m}\le\min(h_0,R/C_*).
\]

If \(C_*=0\), any \(m\) with \(2^{-m}\le h_0\) suffices. If \(R\le0\),
increasing \(m\) cannot make this sufficient bound cross the target, so no
finite \(m\) is guaranteed by it.

---

# Solution to Problem D

All vector operations are over \(\mathbb F_2\), so subtraction equals
addition.

## D.1 Collision characterization

The syndrome class of \(x\) is

\[
\{y:H_k(y)=H_k(x)\}=x+\ker H_k.
\]

The energy decoder returns \(x\) exactly when this coset contains no earlier
element. Such an element exists exactly when some \(y\prec_E x\) satisfies

\[
y+x\in\ker H_k.
\]

Therefore

\[
D_k(H_kx)=x
\iff
\ker H_k\cap S_x=\varnothing.
\]

The first successful depth is the first \(k\) satisfying this condition.
Because nested row prefixes have

\[
\ker H_{k+1}\subseteq\ker H_k,
\]

success persists at every later depth.

## D.2 Sharp finite separation

Fix a nonzero \(v\). For a uniformly random row \(r\in\mathbb F_2^n\),
\(r\cdot v\) is uniform in \(\mathbb F_2\). Hence a random \(k\times n\)
matrix satisfies

\[
\Pr[Hv=0]=2^{-k}.
\]

The union bound gives

\[
\Pr[\ker H\cap S_x\ne\varnothing]
\le|S_x|2^{-k}.
\]

If \(2^k>|S_x|\), this probability is below one, so a successful matrix
exists.

Since

\[
|S_x|=r_E(x)-1,
\]

the choice

\[
k=\lceil\log_2r_E(x)\rceil
\]

satisfies \(2^k\ge r_E(x)>|S_x|\). Also \(r_E(x)\le2^n\), so \(k\le n\).

For a deterministic construction, enumerate all \(k\times n\) binary matrices
in row-major lexicographic order and select the first satisfying
\(Hv\ne0\) for every extensionally enumerable \(v\in S_x\). The exact energy
comparator makes \(S_x\) finitely enumerable, and the probabilistic argument
proves that the search terminates.

Delete rows that lie in the span of earlier retained rows. The retained rows
have the same row space and therefore the same kernel. Extend them, in
lexicographically first order, to a basis of the dual space. Row prefixes of
that basis form the required nested full-rank family.

### Sharpness

Fix a \(d\)-dimensional subspace \(U\le\mathbb F_2^n\) and take \(x=0\).
Supply distinct exact integer energies that place every element of
\(U\setminus\{0\}\) before \(0\), and every element outside \(U\) after \(0\).
Then

\[
S_0=U\setminus\{0\},\qquad r_E(0)=2^d.
\]

If \(\ker H\cap S_0=\varnothing\), the restriction \(H|_U\) is injective.
Therefore its codomain has dimension at least \(d\), so \(H\) has at least
\(d\) rows. The universal bound
\(\lceil\log_2r_E(x)\rceil\) is attained.

## D.3 Uniform residual families

Let \(K=\ker H\). Suppose every coset of \(K\) meets \(B\) at most once. If

\[
z\in K\cap(B-B),
\]

then \(z=u-v\) for \(u,v\in B\), and \(u,v\) lie in the same coset. Hence
\(u=v\) and \(z=0\). Thus

\[
K\cap(B-B)\subseteq\{0\}.
\]

Conversely, if this inclusion holds and \(u,v\in B\) lie in one coset, then
\(u-v\in K\cap(B-B)\), so \(u=v\). This includes \(B=\varnothing\). When
\(B\ne\varnothing\), zero belongs to both \(K\) and \(B-B\), turning inclusion
into equality.

For Hamming balls,

\[
B_r-B_r=B_r+B_r=B_{\min(2r,n)}.
\]

The forward inclusion follows from
\(\operatorname{wt}(u+v)\le\operatorname{wt}(u)+\operatorname{wt}(v)\).
For the reverse inclusion, partition the support of any vector of weight at
most \(2r\) into two sets of size at most \(r\).

Consequently uniqueness on \(B_r\) is equivalent to the absence of a nonzero
kernel vector of weight at most \(2r\), which is

\[
d_{\min}(K)>2r.
\]

When \(2r>n\), this forces \(K=\{0\}\), consistent with
\(d_{\min}(\{0\})=\infty\).

The restriction of \(H\) to \(B_r\) is injective, so

\[
2^k\ge|B_r|=\sum_{i=0}^r\binom ni.
\]

For

\[
B=\bigcup_i(p_i+B_{r_i}),
\]

we have

\[
B-B
=
\bigcup_{i,j}
\left(
p_i+p_j+B_{\min(r_i+r_j,n)}
\right).
\]

Therefore the exact condition is

\[
K\cap
\left(
p_i+p_j+B_{\min(r_i+r_j,n)}
\right)
\subseteq\{0\}
\]

for every ordered pair \((i,j)\).

## D.4 First-hit certificates

If the bounded decoder returns \(x\) at position \(j\), then necessarily

\[
x=y_j,\qquad H(x)=s,
\]

and no earlier candidate has syndrome \(s\). Conversely, those conditions make
the sequential decoder reject positions \(1,\ldots,j-1\) and return \(x\) at
position \(j\). They are therefore necessary and sufficient.

The canonical verifier computes one syndrome at each of
\(y_1,\ldots,y_j\), so a valid certificate uses exactly \(j\) matrix-vector
evaluations under that specified procedure.

This is not an unrestricted lower bound. For example, choose \(j=n+1\)
distinct candidates, \(H=I_n\), \(s=y_j\), and an energy order putting those
candidates first. Their span has dimension at most \(n<j\). A verifier may
evaluate \(H\) on a basis and derive every candidate syndrome by linearity,
using at most \(n\) general matrix-vector evaluations. The canonical count is
exact, but it is model-relative.

---

# Internal verdict

Every fixed theorem in `ACS-MATH-DRAFT-3-WORKING` has a constructive proof.
The strengthened clauses are consistent:

- A's integer penalty has the requested asymptotically sharp family.
- B's sharper interval count follows from totality.
- C separates compatible exact attainment from universal supremal sharpness.
- D's improved logarithmic depth bound is exact on subspace residual sets.

This internal result is evidence that Draft 3 is mathematically coherent. It
is not an independent adversarial review and does not authorize distribution.
