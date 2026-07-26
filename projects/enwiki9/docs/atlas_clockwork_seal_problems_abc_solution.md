# Complete Solutions to Problems A, B, and C

Status: normalized Markdown transcript of a solver submission received through
chat. The mathematical content is preserved, while malformed chat-rendered
LaTeX separators and operators have been normalized. Problems A, B, and C are
treated independently as required by the examination.

Two qualifications emerge:

1. Problems A and B are correct as stated.
2. Problem C's inequalities and constructions are correct. However, C1's
   assertion that the coefficients are "attainable in dimension one" requires
   qualification if it means exact attainment for every arbitrary real
   \(\rho\). Under the rational scalar-coefficient restriction, an irrational
   \(\rho\) need not be attained. The coefficients remain optimal as suprema,
   and exact equality is attained for admissible values such as
   \(\rho=\tfrac12\).

All logarithms below are base two.

---

# Problem A: The Paid-Information Variational Principle

## A0. Preliminary notation

For an assignment

\[
z=(z_1,\ldots,z_J)\in\{1,\ldots,K\}^J,
\]

define

\[
F_z(q)=
\sum_{j=1}^J g_{j,z_j}
+
\sum_{k=1}^K n_k(z)\log q_k,
\]

where a term with \(n_k(z)=0\) is zero even if \(q_k=0\), and a term
with \(n_k(z)>0\) and \(q_k=0\) is \(-\infty\). Since rows can be assigned
independently,

\[
\boxed{\mathcal V_G(q)=\max_z F_z(q).}
\]

Indeed,

\[
\max_zF_z(q)
=
\max_z\sum_{j=1}^J\bigl(g_{j,z_j}+\log q_{z_j}\bigr)
=
\sum_{j=1}^J\max_k\bigl(g_{jk}+\log q_k\bigr).
\]

Ties do not affect the value because every tied maximizer gives the same row
contribution.

## A1. Exact finite duality

### Fixed-count optimization

Fix \(z\), put \(n_k=n_k(z)\), and let \(p_k=n_k/J\). Then

\[
\max_{q\in\Delta_K}\sum_{k:n_k>0}n_k\log q_k
=
\sum_{k:n_k>0}n_k\log\frac{n_k}{J},
\]

with the unique maximizing vector

\[
\boxed{q_k=\frac{n_k}{J}}
\]

for every \(k\), including \(q_k=0\) when \(n_k=0\).

To prove this, let \(S=\{k:n_k>0\}\), set

\[
Q=\sum_{k\in S}q_k\le1,
\qquad
r_k=\frac{q_k}{Q},
\]

and observe

\[
\sum_{k\in S}n_k\log q_k
=
J\log Q+J\sum_{k\in S}p_k\log r_k.
\]

Gibbs' inequality gives

\[
\sum_{k\in S}p_k\log r_k
\le
\sum_{k\in S}p_k\log p_k,
\]

with equality precisely when \(r=p\). Also \(\log Q\le0\), with equality
precisely when \(Q=1\). The positive coordinates therefore equal \(p_k\)
and already sum to one, forcing all unused coordinates to zero.

Because the assignment set is finite,

\[
\begin{aligned}
\max_{q\in\Delta_K}\mathcal V_G(q)
&=\max_q\max_zF_z(q)\\
&=\max_z\max_qF_z(q)\\
&=
\boxed{
\max_z\left[
\sum_{j=1}^Jg_{j,z_j}
+
\sum_{k:n_k(z)>0}n_k(z)\log\frac{n_k(z)}J
\right].
}
\end{aligned}
\]

The right side is a maximum over finitely many assignments, and the fixed-count
argument supplies an optimizer \(q_k=n_k(z)/J\). Thus the relaxed maximum
exists.

Let the common optimal value be \(M\). If \(q\) is optimal and \(z\) is any
rowwise maximizing assignment at \(q\), then

\[
F_z(q)=\mathcal V_G(q)=M.
\]

Since \(\max_{q'}F_z(q')\le M\), the same \(q\) maximizes \(F_z\), and the
fixed-count result forces \(q_k=n_k(z)/J\). Conversely, if \(z\) is dual
optimal and \(q_k=n_k(z)/J\), then \(F_z(q)=M\) and
\(\mathcal V_G(q)\ge M\). No relaxed value exceeds \(M\), so \(q\) is
optimal. If \(z\) were not rowwise maximizing there, the value would exceed
\(M\), a contradiction. Hence

\[
\boxed{
q\text{ is optimal}
\iff
\exists\text{ a dual-optimal rowwise assignment }z
\text{ with }q_k=n_k(z)/J.
}
\]

In fact, every rowwise maximizing assignment at an optimal \(q\) has these
counts. Consequently, an explanation has zero optimal weight exactly when it
has zero count in the associated optimizing assignment. Every positive weight
belongs to \(\{1/J,2/J,\ldots,1\}\), and positive weights sum to one.

## A2. Integer prefix penalty

For any legal integer length vector \(\ell\), define \(q_k=2^{-\ell_k}\),
with \(2^{-\infty}=0\). Kraft's inequality gives \(q\in\Delta_K\), and

\[
g_{jk}-\ell_k=g_{jk}+\log q_k.
\]

Therefore

\[
V_G(\ell)=\mathcal V_G(q)\le\mathcal V^*(G),
\]

and hence

\[
\boxed{V^*(G)\le\mathcal V^*(G).}
\]

Now let \(q^*\) optimize the relaxed problem and define

\[
\ell_k=
\begin{cases}
\lceil-\log q_k^*\rceil,&q_k^*>0,\\
\infty,&q_k^*=0.
\end{cases}
\]

Zero-weight explanations remain inactive. Since
\(2^{-\ell_k}\le q_k^*\), Kraft's inequality holds. Moreover,

\[
-\ell_k\ge\log q_k^*-1.
\]

For each row,

\[
\max_k(g_{jk}-\ell_k)
\ge
\max_k(g_{jk}+\log q_k^*)-1.
\]

Summing over \(J\) rows yields

\[
\boxed{
\mathcal V^*(G)-J\le V^*(G)\le\mathcal V^*(G).
}
\]

To realize the lengths as an actual prefix code, order active indices so that
\(L_1\le\cdots\le L_r\), define

\[
C_1=0,
\qquad
C_i=(C_{i-1}+1)2^{L_i-L_{i-1}},
\]

and assign the \(L_i\)-bit representation of \(C_i\). Inductively,

\[
\frac{C_i}{2^{L_i}}=\sum_{h<i}2^{-L_h}.
\]

Kraft's inequality implies \(0\le C_i<2^{L_i}\). The corresponding dyadic
intervals are disjoint, so the codewords are prefix-free. If an active word has
length zero, Kraft's inequality forces it to be the sole active word, represented
by the empty word.

## A3. Description-priced explanations

For a count vector \(n\), let \(S(n)=\{k:n_k>0\}\). Coordinates outside
\(S(n)\) may be set to infinity without changing the objective, so

\[
L(n)=
\min\left\{
\sum_{k\in S(n)}n_k\ell_k:
\sum_{k\in S(n)}2^{-\ell_k}\le1
\right\}.
\]

A feasible vector is

\[
\ell_k^{(0)}=
\left\lceil-\log\frac{n_k}{J}\right\rceil.
\]

Let \(U=\sum_{k\in S(n)}n_k\ell_k^{(0)}\). Any minimizer of cost at most
\(U\) satisfies

\[
0\le\ell_k\le\left\lfloor\frac{U}{n_k}\right\rfloor.
\]

It therefore suffices to inspect the finite Cartesian product of these ranges,
discard tuples violating Kraft's inequality, and select the feasible tuple with
least weighted length. The displayed feasible vector proves nonemptiness, so
the minimum exists. The canonical construction from A2 then produces an actual
prefix code.

For fixed \(z\),

\[
V_{G,d}(\ell,z)
=
\sum_jg_{j,z_j}
-
\sum_kn_k(z)\ell_k
-
\sum_{k:n_k(z)>0}d_k.
\]

Only the middle term depends on \(\ell\), hence

\[
\max_\ell V_{G,d}(\ell,z)
=
\sum_jg_{j,z_j}
-L(n(z))
-
\sum_{k:n_k(z)>0}d_k.
\]

There are finitely many assignments, so

\[
\boxed{
\max_{\ell,z}V_{G,d}(\ell,z)
=
\max_z\left[
\sum_jg_{j,z_j}
-L(n(z))
-
\sum_{k:n_k(z)>0}d_k
\right].
}
\]

Consequently, either side exceeds a real threshold \(D\) if and only if the
other does. This is the exact necessary-and-sufficient threshold theorem.

## A4. Stability under perturbation

If \(\max_{j,k}|g_{jk}-g'_{jk}|\le\varepsilon\), then for every fixed
\(\ell\) and row \(j\),

\[
\left|
\max_k(g_{jk}-\ell_k)-\max_k(g'_{jk}-\ell_k)
\right|
\le\varepsilon.
\]

Summation and taking suprema in both directions gives

\[
\boxed{|V^*(G)-V^*(G')|\le J\varepsilon.}
\]

The coefficient is sharp: setting \(g'_{jk}=g_{jk}+\varepsilon\) for all
\(j,k\) gives

\[
V_{G'}(\ell)=V_G(\ell)+J\varepsilon
\]

for every legal \(\ell\), and therefore equality in the bound.

---

# Problem B: The Predictive Wheeler-Quotient Theorem

For convenience define

\[
o_h(u)=c(T(h,u)).
\]

Equality of all traces is equivalent to \(o_h(u)=o_{h'}(u)\) for all
\(u\in A^*\), because trace entries are terminal outputs of prefixes.

## B1. Myhill-Nerode characterization

If \(h\equiv h'\), taking \(u=\epsilon\) gives \(c(h)=c(h')\). For every
\(a\in A\) and \(u\in A^*\),

\[
o_{T(h,a)}(u)=o_h(au)=o_{h'}(au)=o_{T(h',a)}(u),
\]

so \(T(h,a)\equiv T(h',a)\). Thus \(\equiv\) is a color-preserving right
congruence, and the quotient transition and color are well-defined.

If \(R\) is any color-preserving right congruence and \(hRh'\), induction on
\(|u|\) gives \(T(h,u)R T(h',u)\), and color preservation gives equal
terminal outputs for every \(u\). Hence \(R\subseteq\equiv\), proving

\[
\boxed{\equiv\text{ is the unique coarsest color-preserving right congruence.}}
\]

Unequal quotient classes are not behaviorally equivalent, so some finite word
distinguishes them.

Let \(N=|Q|\ge2\), and define on \(Q\)

\[
q\sim_rq'
\iff
c(T(q,u))=c(T(q',u))
\quad\text{for every }|u|\le r.
\]

The relations refine with \(r\). If \(\sim_{r+1}=\sim_r\), then
\(\sim_r\) is a color-preserving right congruence: equality through length
\(r+1\) implies successor states agree through length \(r\). Since \(Q\) is
the behavioral quotient, stabilization is possible only at equality.

Let \(m\) be the shortest distinguishing length for two unequal states. If
\(m>0\), those states remain together under \(\sim_{m-1}\), so each refinement
from \(\sim_0\) through \(\sim_m\) is strict. The initial color partition has
at least two blocks; otherwise the universal relation would be a nontrivial
color-preserving right congruence. If \(b_r\) is the number of blocks, then

\[
N\ge b_m\ge b_0+m\ge2+m,
\]

and therefore

\[
\boxed{m\le N-2.}
\]

This is sharp. Let

\[
Q_N=\{0,1,\ldots,N-1\},\qquad A=\{a\},
\]

with

\[
T(i,a)=\min(i+1,N-1),
\qquad
c(i)=\mathbf1\{i=N-1\}.
\]

All states are behaviorally distinct. States zero and one first differ after
\(a^{N-2}\), so their shortest distinguishing word has length \(N-2\).

A finite minimality certificate selects one representative for each quotient
class and one distinguishing word, of length at most \(N-2\), for each
unordered pair. Verifying the terminal colors for every listed pair prevents
any two classes from being identified by a color-preserving right congruence.

## B2. Wheeler interval theorem

For \(a\in A\), write \(T_a(q)=T(q,a)\), so \(I(a)=T_a(Q)\).

Assume the order is Wheeler. Indegree-zero vertices come first by definition.
For \(a<a'\), every target in \(I(a)\) precedes every target in \(I(a')\), so

\[
\max I(a)<\min I(a')
\]

when both are nonempty. Equal-label Wheeler monotonicity says every \(T_a\) is
nondecreasing.

To prove \(I(a)\) is an interval, take \(x<y<z\) with \(x,z\in I(a)\).
The middle vertex has positive indegree because all zero-indegree vertices
precede \(x\). Let an incoming edge to \(y\) have label \(b\). If \(b<a\),
label ordering forces \(y<x\); if \(b>a\), it forces \(z<y\). Both are
impossible, so \(b=a\) and \(y\in I(a)\).

Conversely, suppose zero-indegree vertices come first, the one-letter images
are intervals strictly ordered by label, and each \(T_a\) is nondecreasing.
The label ordering is Wheeler condition 2, and monotonicity is Wheeler condition
3. Thus the formulations are equivalent.

For the extension to words, use the following lemma: if \(f\) is nondecreasing
on a finite chain and \(f(Q)\) is an interval, then \(f(J)\) is an interval
for every interval \(J\). Indeed, if \(f(p)\le y\le f(r)\) for the endpoints
of \(J\), full-image intervality provides an \(x\) with \(f(x)=y\).
Monotonicity puts an interior preimage inside \(J\), while endpoint values are
already attained at \(p\) or \(r\).

Now \(I(\epsilon)=Q\), and

\[
I(wa)=T_a(I(w)).
\]

Induction with the lemma proves

\[
\boxed{I(w)\text{ is an interval for every }w\in A^*.}
\]

## B3. Canonical finite Wheeler unfolding

Fix \(L\ge0\). Let

\[
U_L=Q\times A^{\le L},
\]

with edges

\[
(q,w)\xrightarrow a(q,wa)
\quad\text{when }|w|<L.
\]

Order words colexicographically, breaking equal-word ties by the fixed order on
\(Q\). Vertices \((q,\epsilon)\) are exactly the zero-indegree vertices and
come first.

If \(a<a'\), the reversed target words begin with \(a\) and \(a'\), so every
\(a\)-target precedes every \(a'\)-target. For equal labels, prepending the
same letter to reversed words preserves their lexicographic order; when source
words agree, the \(Q\)-tie order is preserved. The unfolding is therefore
Wheeler.

Tag each vertex by

\[
\tau(q,w)=T(q,w)\in Q.
\]

No vertices are merged, so behaviorally unequal terminal tags remain explicitly
distinct.

There are \(|A|^i\) words of length \(i\), hence

\[
\boxed{|U_L|=|Q|\sum_{i=0}^{L}|A|^i.}
\]

Each vertex below depth \(L\) has \(|A|\) outgoing edges, giving

\[
\boxed{|E_L|=|Q|\sum_{i=1}^{L}|A|^i.}
\]

For a continuation \(u\), endpoints of represented \(u\)-paths have word
components ending in \(u\). Their reversals share prefix \(u^{\rm rev}\), so
they form a lexicographic interval; consequently the original endpoint set is
a colexicographic interval. Each word carries one contiguous \(Q\)-block, so
the full endpoint set is an interval.

A finite certificate consists of the ordered vertex list, all terminal tags,
and the complete edge list. The three Wheeler conditions can be checked
directly from these finite objects.

## B4. Continuation multiplicity bound

A nonempty interval in an \(N\)-element chain is determined by its endpoints,
so there are \(N(N+1)/2\) nonempty intervals. Including the empty set gives

\[
\boxed{
|\{I(w):w\in A^*\}|
\le1+\frac{N(N+1)}2.
}
\]

Because \(T\) is total and \(Q\ne\varnothing\), every \(I(w)\) is actually
nonempty here, so the extra one is unnecessary.

For a matching order-dependent lower family, take

\[
Q=\{1,\ldots,N\},
\qquad
T(i,a)=\min(i+1,N),
\]

with only state \(N\) assigned a distinct color. State one is the unique
zero-indegree vertex, \(T_a\) is nondecreasing, and \(I(a)=\{2,\ldots,N\}\),
so the natural order is Wheeler. For \(0\le t\le N-1\),

\[
I(a^t)=\{t+1,\ldots,N\}.
\]

These are \(N\) distinct intervals, proving no bound independent of \(N\) is
possible.

---

# Problem C: Integer Shadowing of Selective Recurrences

Let \(h=2^{-m}\). Nearest-coordinate rounding to \(h\mathbb Z^d\) changes
each coordinate by at most \(h/2\), so

\[
\boxed{
\|R_m(v)-v\|_2\le\sqrt d\,2^{-m-1}=\eta_m.
}
\]

## C1. Uniform shadowing

Let \(e_t=\|s_t-\widehat s_t\|_2\) and put

\[
\widetilde s_{t+1}
=
\widehat A_{a_t}\widehat s_t+
\widehat b_{a_t}.
\]

Then

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
\rho e_t+
\varepsilon_AS+
\varepsilon_b+
\eta_m.
\]

Writing \(\delta=\varepsilon_AS+\varepsilon_b+\eta_m\) and iterating gives

\[
\boxed{
e_t
\le
\rho^{t-1}e_1
+
\frac{1-\rho^{t-1}}{1-\rho}\delta.
}
\]

The estimate is uniform over all input sequences.

For exact scalar equality at an admissible contraction, take dimension one, one
symbol, an upward half-grid tie rule, and

\[
\rho=\frac12,
\quad
A=\widehat A=\frac12,
\quad
\widehat b=0,
\quad
b=-\beta,
\]

where \(\beta\ge0\) is rational. Initialize

\[
\widehat s_1=h,
\qquad
s_1=h-e_1.
\]

Since \(R_m(h/2)=h\), the shadow state remains \(h\). For
\(d_t=\widehat s_t-s_t\),

\[
d_{t+1}=\frac12d_t+\beta+\frac h2.
\]

Here \(\eta_m=h/2\), \(\varepsilon_A=0\), and
\(\varepsilon_b=\beta\), so equality holds in the C1 bound.

There is a necessary qualification for an arbitrary irrational \(\rho\).
Every scalar true coefficient is rational, so its absolute value cannot equal,
for example, \(1/\sqrt2\). Exact attainment at every arbitrary real \(\rho\)
is therefore impossible under the stated rationality restriction.

The coefficients remain optimal suprema. For any dyadic \(r<\rho\) tending to
\(\rho\), take \(A=\widehat A=r\), zero biases, and a nonzero initial error;
then \(e_t=r^{t-1}e_1\), approaching the initial-error coefficient. For the
accumulated coefficient, take equal coefficient \(r\), true bias \(\beta\),
shadow bias zero, and equal zero initial states. Then

\[
e_t=\beta\sum_{i=0}^{t-2}r^i.
\]

Letting \(r\uparrow\rho\), and taking \(\beta\) large relative to the fixed
rounding allowance when necessary, proves no smaller universal geometric
coefficient is valid. Thus exact equality is attained whenever the contraction
bound itself is admissible, while the displayed constants are supremally sharp
for every real \(\rho\in[0,1)\).

## C2. Cumulative logistic-loss transfer

For

\[
\lambda(x,y)=\log_2(1+e^y)-\frac{xy}{\ln2},
\]

we have

\[
\frac{\partial\lambda}{\partial y}
=
\frac1{\ln2}\left(\frac{e^y}{1+e^y}-x\right).
\]

For \(x=0\), the derivative magnitude tends to \(1/\ln2\) as
\(y\to+\infty\); for \(x=1\), it tends to the same value as
\(y\to-\infty\). Therefore

\[
\boxed{\operatorname{Lip}_y\lambda(x,\cdot)=\frac1{\ln2}}
\]

uniformly in \(x\), and the constant is sharp.

The logit difference satisfies

\[
\begin{aligned}
\widehat y_t-y_t
={}&(\widehat c-c)^T\widehat s_t
+c^T(\widehat s_t-s_t)
+\widehat\gamma_{a_t}-\gamma_{a_t},
\end{aligned}
\]

so

\[
|\widehat y_t-y_t|
\le
\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma.
\]

Lipschitz continuity and summation give

\[
\boxed{
\sum_{t=1}^n
[\lambda(x_t,\widehat y_t)-\lambda(x_t,y_t)]
\le
\frac1{\ln2}\sum_{t=1}^n
(\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma).
}
\]

Using C1,

\[
\sum_{t=1}^ne_t
\le
e_1\frac{1-\rho^n}{1-\rho}
+
\frac{\delta}{1-\rho}
\left[n-\frac{1-\rho^n}{1-\rho}\right].
\]

Thus

\[
\boxed{
\begin{aligned}
&\sum_{t=1}^n
[\lambda(x_t,\widehat y_t)-\lambda(x_t,y_t)]\\
&\le\frac1{\ln2}\Bigg[
n(\varepsilon_cS+\varepsilon_\gamma)
+\|c\|_2e_1\frac{1-\rho^n}{1-\rho}\\
&\qquad+
\frac{\|c\|_2\delta}{1-\rho}
\left(n-\frac{1-\rho^n}{1-\rho}\right)
\Bigg].
\end{aligned}
}
\]

## C3. Householder realization

For a real \(d\times d\) matrix \(M\), entrywise nearest dyadic rounding
changes each entry by at most \(2^{-m-1}\). Therefore

\[
\boxed{
\|Q_m(M)-M\|_2
\le\|Q_m(M)-M\|_F
\le d\,2^{-m-1}=\eta_{A,m}.
}
\]

Let

\[
P=\prod_{j=1}^kH_j,
\qquad
\widehat P=\prod_{j=1}^k\widehat H_j.
\]

Every \(H_j\) is orthogonal, while
\(\|\widehat H_j\|_2\le1+\varepsilon_H\). The telescoping product identity
gives

\[
\|\widehat P-P\|_2
\le
\sum_{i=1}^k(1+\varepsilon_H)^{i-1}\varepsilon_H
=
(1+\varepsilon_H)^k-1.
\]

Since

\[
\widetilde A-A
=(\widehat D-D)\widehat P
+D(\widehat P-P)
+(\widehat E-E),
\]

we obtain

\[
\boxed{
\|\widehat A-A\|_2
\le
\varepsilon_D(1+\varepsilon_H)^k
+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E+
\eta_{A,m}.
}
\]

Now let \(Q\in\mathbb Q^{d\times d}\) be orthogonal. We prove by induction on
\(d\) that it is a product of at most \(d\) rational Householder reflections.
If \(Qe_1=e_1\), then \(Q\) preserves \(e_1^\perp\) and has block form
\(1\oplus Q'\), where \(Q'\in O_{d-1}(\mathbb Q)\); apply induction.
Otherwise set

\[
v=Qe_1-e_1
\]

and

\[
H_v=I-2\frac{vv^T}{v^Tv}.
\]

The vector and reflection are rational. Since

\[
v^TQe_1=1-e_1^TQe_1,
\qquad
v^Tv=2(1-e_1^TQe_1),
\]

we have \(H_vQe_1=e_1\). The matrix \(H_vQ\) therefore factors into at
most \(d-1\) rational reflections by induction, and
\(Q=H_v(H_vQ)\) uses at most \(d\). Hence

\[
\boxed{
O_d(\mathbb Q)\text{ is generated by at most }d
\text{ rational Householder reflections.}
}
\]

## C4. Precision threshold

Let

\[
\delta_A=
\varepsilon_D(1+\varepsilon_H)^k
+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E+d\,2^{-m-1}
\]

and

\[
\varepsilon_{\rm step}=\delta_AS+\varepsilon_b+\eta_m.
\]

C1 gives the simpler uniform estimate

\[
e_t\le e_1+\frac{\varepsilon_{\rm step}}{1-\rho}.
\]

C2 therefore proves that

\[
\boxed{
\frac n{\ln2}\left[
\varepsilon_cS+\varepsilon_\gamma
+\|c\|_2\left(e_1+\frac{\varepsilon_{\rm step}}{1-\rho}\right)
\right]
\le\varepsilon
}
\]

is sufficient for cumulative excess logistic loss at most \(\varepsilon\).

For explicit nearest-dyadic bounds, write \(u=2^{-m}\). Scalar rounding gives
\(|Q_m(x)-x|\le u/2\), vector rounding in \(\mathbb R^r\) gives

\[
\|Q_m(v)-v\|_2\le\frac{\sqrt r\,u}{2},
\]

and matrix rounding in \(\mathbb R^{r\times s}\) gives

\[
\|Q_m(M)-M\|_2
\le\|Q_m(M)-M\|_F
\le\frac{\sqrt{rs}\,u}{2}.
\]

For a \(d\times d\) matrix this is \(du/2\); for a diagonal matrix the
sharper operator bound is \(u/2\).

If all coefficients and the initial state are nearest-rounded at precision
\(m\), then

\[
\varepsilon_D\le\frac u2,
\quad
\varepsilon_H\le\frac{du}{2},
\quad
\varepsilon_E\le\frac{du}{2},
\]

and

\[
\varepsilon_b,\varepsilon_c,e_1\le\frac{\sqrt d\,u}{2},
\qquad
\varepsilon_\gamma\le\frac u2.
\]

Consequently,

\[
\delta_A(u)
\le
\frac u2\left(1+\frac{du}{2}\right)^k
+d_0\left[\left(1+\frac{du}{2}\right)^k-1\right]
+du.
\]

Impose \(kdu/2\le1\). Then

\[
\left(1+\frac{du}{2}\right)^k\le e,
\qquad
\left(1+\frac{du}{2}\right)^k-1\le e\frac{kdu}{2}.
\]

Thus \(\delta_A(u)\le C_Au\), where

\[
\boxed{C_A=d+\frac e2(1+d_0kd).}
\]

It follows that

\[
\varepsilon_{\rm step}\le u(SC_A+\sqrt d).
\]

The sufficient loss bracket is at most \(uC_{\rm tot}\), where

\[
\boxed{
C_{\rm tot}
=
\frac{S\sqrt d}{2}+rac12
+\|c\|_2\left[
\frac{\sqrt d}{2}
+\frac{SC_A+\sqrt d}{1-\rho}
\right].
}
\]

For \(\varepsilon>0\), a fully explicit sufficient precision is

\[
\boxed{
m\ge
\max\left\{
1,
\left\lceil\log_2^+\frac{kd}{2}\right\rceil,
\left\lceil\log_2^+\frac{nC_{\rm tot}}{\varepsilon\ln2}\right\rceil
\right\},
}
\]

where \(\log_2^+(x)=\max\{0,\log_2x\}\), and the middle term is omitted when
\(k=0\). This simultaneously guarantees the product guard and the requested
loss bound.

If the initial state is not nearest-rounded, retain \(e_1\) explicitly. Put

\[
C_0=
\frac{S\sqrt d}{2}+rac12
+\frac{\|c\|_2(SC_A+\sqrt d)}{1-\rho}
\]

and

\[
R=\frac{\varepsilon\ln2}{n}-\|c\|_2e_1.
\]

When \(R>0\), it suffices to take

\[
\boxed{
m\ge
\max\left\{
1,
\left\lceil\log_2^+\frac{kd}{2}\right\rceil,
\left\lceil\log_2^+\frac{C_0}{R}\right\rceil
\right\}.
}
\]

If \(R\le0\), coefficient precision alone cannot overcome the initial-state
term in this sufficient estimate.

---

# Final verdict

**Problem A:** Every requested claim is true. The relaxed optimizer is an
empirical assignment distribution \(n_k/J\); integer prefix coding loses less
than one bit per block; the description-priced criterion is exact; and the
perturbation coefficient \(J\) is sharp.

**Problem B:** Every requested principal claim is true. Behavioral equivalence
is the coarsest color-preserving right congruence; the \(|Q|-2\)
distinguishing bound is sharp; Wheeler orders are exactly the stated
interval-monotonicity orders; the colex unfolding is Wheeler; and continuation
sets are intervals. Because the transition is total, B4 can omit the extra
empty-set term.

**Problem C:** The shadowing, loss-transfer, Householder perturbation, rational
factorization, and precision-threshold theorems are valid. The correction is
that exact scalar attainment at a displayed arbitrary irrational \(\rho\)
cannot be demanded while scalar recurrent coefficients are rational. Exact
attainment occurs for admissible values such as \(\rho=\tfrac12\), and the
stated coefficients are optimal suprema for all \(\rho\).
