# The Atlas and Clockwork Mathematical Examination

Distribution status: `DRAFT - EXPERT REVIEW ONLY`
Problem version: `ACS-MATH-DRAFT-3-WORKING`

This is a new problem-bank artifact. It does not modify or supersede the
immutable submissions governed by Draft 1 or Draft 2. It is not a candidate
examination, and no Seal or application transfer is implied.

## Instructions

This is a pencil-and-paper examination in finite mathematics. The four
problems are logically independent. A complete solution to any one problem is
an independent complete submission.

Every construction must be finite and deterministic from the stated input.
Every canonical choice uses the orders supplied in its problem. A
counterexample is a solution only to a clause explicitly marked `PROVE OR
DISPROVE`.

No program, dataset, experiment, benchmark, or application artifact is part of
the examination. All logarithms are base two unless stated otherwise.

---

# Problem A: Prefix-Paid Information

## A.1 Definitions

Let \(J,K\ge1\) and \(G=(g_{jk})\in\mathbb R^{J\times K}\). A legal extended
length vector is

\[
\ell\in(\mathbb Z_{\ge0}\cup\{\infty\})^K,\qquad
\sum_k2^{-\ell_k}\le1,
\]

with at least one finite coordinate. Use \(2^{-\infty}=0\). Define

\[
V_G(\ell)=\sum_{j=1}^J\max_k(g_{jk}-\ell_k),
\qquad
V^*(G)=\sup_\ell V_G(\ell).
\]

Let

\[
\Delta_K=\{q\in[0,1]^K:\sum_kq_k\le1\}.
\]

Use \(\log0=-\infty\), set
\(\mathcal V_G(0,\ldots,0)=-\infty\), and otherwise define

\[
\mathcal V_G(q)=\sum_{j=1}^J\max_k(g_{jk}+\log q_k).
\]

For \(z\in\{1,\ldots,K\}^J\), let
\(n_k(z)=|\{j:z_j=k\}|\), with \(0\log0=0\).

## A.2 Exact duality and optimizers

Prove

\[
\max_{q\in\Delta_K}\mathcal V_G(q)
=
\max_z\left[
\sum_jg_{j,z_j}
+\sum_{k:n_k(z)>0}n_k(z)\log\frac{n_k(z)}J
\right].
\]

Prove optimizer existence and the following exact characterization:
\(q\) is optimal if and only if some dual-optimal assignment selected from
the rowwise maximizers at \(q\) satisfies

\[
q_k=\frac{n_k(z)}J
\]

for every \(k\). Characterize all zero coordinates and all tie cases.

## A.3 Integer penalty and sharpness

Writing \(\mathcal V^*(G)=\max_q\mathcal V_G(q)\), prove

\[
\mathcal V^*(G)-J\le V^*(G)\le\mathcal V^*(G).
\]

Construct a canonical binary prefix code from an optimal \(q\), leaving zero
coordinates inactive. Then prove asymptotic sharpness of the coefficient one:
construct a sequence \((J_r,K_r,G_r)\) for which

\[
\frac{\mathcal V^*(G_r)-V^*(G_r)}{J_r}\longrightarrow1.
\]

## A.4 Exact finite prefix price

For \(n\in\mathbb Z_{\ge0}^K\) with \(\sum_kn_k=J\), define

\[
L(n)=\min_{\ell:\,\sum_k2^{-\ell_k}\le1}
\sum_{k:n_k>0}n_k\ell_k,
\]

with zero-count coordinates inactive. Prove:

1. The minimum exists.
2. For support size at least two, \(L(n)\) equals the weighted external path
   length produced by binary Huffman merging of the positive counts.
3. A fixed tie order yields a canonical optimal code.
4. For support size one, the unique active word has length zero.

Let \(d_k\ge0\). Prove the exact threshold equivalence

\[
\max_{\ell,z}
\left[
\sum_j(g_{j,z_j}-\ell_{z_j})
-\sum_{k:n_k(z)>0}d_k
\right]>D
\]

if and only if

\[
\max_z\left[
\sum_jg_{j,z_j}
-L(n(z))
-\sum_{k:n_k(z)>0}d_k
\right]>D.
\]

## A.5 Stability

If \(\max_{j,k}|g_{jk}-g'_{jk}|\le\varepsilon\), prove

\[
|V^*(G)-V^*(G')|\le J\varepsilon,
\]

and give equality cases proving that \(J\) is the smallest universal
coefficient.

---

# Problem B: Predictive Quotients and Wheeler Geometry

## B.1 Behavioral quotient

Let \(H\ne\varnothing\) be finite, let \(A\) be a finite totally ordered
alphabet, let \(T:H\times A\to H\) be total and deterministic, and let
\(c:H\to C\) be a finite coloring. Extend \(T\) to words and define

\[
h\equiv h'
\iff
\forall u\in A^*,\quad
\bigl(c(T(h,v))\bigr)_{v\preceq u}
=
\bigl(c(T(h',v))\bigr)_{v\preceq u},
\]

where \(v\preceq u\) ranges over prefixes in increasing length. Put
\(Q=H/{\equiv}\).

Prove that \(\equiv\) is the unique coarsest color-preserving right
congruence. Prove that unequal quotient states have a distinguishing word of
length at most \(|Q|-2\) when \(|Q|\ge2\), and construct a family attaining
the bound.

Give a finite minimality certificate with one representative per class and
one distinguishing word per unordered pair. Bound its total word length by

\[
\binom{|Q|}{2}(|Q|-2).
\]

## B.2 Wheeler characterization

Form the labeled quotient graph with edges

\[
q\xrightarrow a\overline T(q,a).
\]

A total order is Wheeler when indegree-zero states come first, smaller labels
have smaller targets, and equal-label edges preserve source order weakly.
For \(w\in A^*\), define

\[
I(w)=\{\overline T(q,w):q\in Q\}.
\]

Prove that an order is Wheeler if and only if:

1. indegree-zero vertices come first;
2. every \(I(a)\) is an interval;
3. nonempty \(I(a)\) occur in strict alphabet order;
4. \(q\mapsto\overline T(q,a)\) is nondecreasing for every \(a\).

Prove that every \(I(w)\) is then a nonempty interval.

## B.3 Finite order-relative unfolding

Fix \(L\in\mathbb Z_{\ge0}\) and a total order on \(Q\). Define vertices
\((q,w)\in Q\times A^{\le L}\), edges

\[
(q,w)\xrightarrow a(q,wa)\qquad(|w|<L),
\]

and terminal tags \(\overline T(q,w)\). Order first by colexicographic word
order and then by the supplied state order.

Prove that the unfolding is Wheeler, retains distinct tagged terminal
behaviors, and has exactly

\[
|Q|\sum_{i=0}^L|A|^i
\quad\text{vertices},\qquad
|Q|\sum_{i=1}^L|A|^i
\quad\text{edges}.
\]

For \(u\in A^{\le L}\), prove that

\[
J_L(u)=\{(q,wu):q\in Q,\ |w|+|u|\le L\}
\]

is one interval. Specify a finite certificate and a direct verifier.

## B.4 Continuation multiplicity

Prove the sharper total-system bound

\[
\left|\{I(w):w\in A^*\}\right|
\le\frac{|Q|(|Q|+1)}2.
\]

Construct, for every \(N\ge1\), a total Wheeler system with \(N\) states and
at least \(N\) distinct continuation intervals. Explain precisely why the
empty-set term required for partial systems is absent here.

---

# Problem C: Integer Shadowing of Contractive Selective Recurrences

## C.1 System and invariant bounds

Let \(d,n\ge1\), let \(\mathcal A\) be finite, and let

\[
s_{t+1}=A_{a_t}s_t+b_{a_t},\qquad
y_t=c^Ts_t+\gamma_{a_t},
\]

where all displayed coefficients are rational and
\(\|A_a\|_2\le\rho<1\). Prove that if \(\|b_a\|_2\le B\), then

\[
\|s_t\|_2
\le
\rho^{t-1}\|s_1\|_2+
\frac{1-\rho^{t-1}}{1-\rho}B.
\]

State and prove the corresponding bound for any approximating recurrence.

For \(m\ge1\), let \(R_m\) round coordinatewise to
\(2^{-m}\mathbb Z^d\) with a fixed tie rule, and prove

\[
\|R_m(v)-v\|_2\le\eta_m:=\sqrt d\,2^{-m-1}.
\]

## C.2 Uniform shadowing and correct sharpness

Assume

\[
\|s_t\|_2,\|\widehat s_t\|_2\le S,\quad
\|A_a-\widehat A_a\|_2\le\varepsilon_A,\quad
\|b_a-\widehat b_a\|_2\le\varepsilon_b.
\]

For

\[
\widehat s_{t+1}
=R_m(\widehat A_{a_t}\widehat s_t+\widehat b_{a_t}),
\qquad
e_t=\|s_t-\widehat s_t\|_2,
\]

prove

\[
e_t\le
\rho^{t-1}e_1+
\frac{1-\rho^{t-1}}{1-\rho}
(\varepsilon_AS+\varepsilon_b+\eta_m).
\]

Give one explicit nontrivial scalar lattice construction, such as
\(\rho=\tfrac12\) with a stated tie rule, attaining equality in both
coefficients. For every real \(\rho\in[0,1)\), prove only the universally valid
claim: the two coefficients are sharp suprema over admissible rational scalar
contractions approaching \(\rho\). Do not assert exact attainment for every
rational \(\rho\).

## C.3 Logistic loss

For

\[
\lambda(x,y)=\log_2(1+e^y)-\frac{xy}{\ln2},
\qquad x\in\{0,1\},
\]

prove that the sharp global Lipschitz constant in \(y\) is \(1/\ln2\). If

\[
\|c-\widehat c\|_2\le\varepsilon_c,\qquad
|\gamma_a-\widehat\gamma_a|\le\varepsilon_\gamma,
\]

prove

\[
\sum_{t=1}^n
[\lambda(x_t,\widehat y_t)-\lambda(x_t,y_t)]
\le
\frac1{\ln2}\sum_{t=1}^n
(\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma),
\]

then substitute C2 and evaluate every geometric sum.

## C.4 Rational Householder realization

Suppose

\[
A=D\prod_{j=1}^kH_j+E,\qquad
H_j=I-2\frac{v_jv_j^T}{v_j^Tv_j},
\]

is supplied exactly over \(\mathbb Q\). With

\[
\|\widehat D-D\|_2\le\varepsilon_D,\quad
\|\widehat H_j-H_j\|_2\le\varepsilon_H,\quad
\|\widehat E-E\|_2\le\varepsilon_E,\quad
\|D\|_2\le d_0,
\]

let

\[
\widehat A=
Q_m\left(\widehat D\prod_{j=1}^k\widehat H_j+\widehat E\right),
\]

where products use exact widened intermediates and \(Q_m\) rounds only the
stored result. Prove

\[
\|Q_m(M)-M\|_2\le d\,2^{-m-1}
\]

and

\[
\|\widehat A-A\|_2
\le
\varepsilon_D(1+\varepsilon_H)^k
+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E+d\,2^{-m-1}.
\]

Prove that every rational orthogonal \(d\times d\) matrix is a product of at
most \(d\) rational Householder reflections.

## C.5 Finite precision

Derive a closed explicit sufficient lower bound on \(m\) guaranteeing total
excess logistic loss at most a supplied \(\varepsilon>0\) when every
coefficient and the initial state are nearest-\(m\)-dyadic approximations.

Then allow \(e_1\) and any subset of coefficient errors to be externally
fixed. Separate the \(m\)-independent loss floor, prove the exact strict
feasibility condition required by your sufficient bound, and derive a finite
lower bound on \(m\) only when that condition holds.

---

# Problem D: Energy-Ordered Parity Separation

## D.1 Ordered space

Let \(X=\mathbb F_2^n\). The input supplies a finite exact representation of
\(E:X\to\mathbb R\) and a decidable exact comparator. Order \(X\) by increasing
energy and lexicographic ties. Define

\[
r_E(x)=1+|\{y:y\prec_E x\}|,
\qquad
S_x=\{y+x:y\prec_E x\}.
\]

Let \(H_0,\ldots,H_n\) be nested row-prefix linear maps, with \(H_n\) full
rank, and define

\[
D_k(s)=\min_{\prec_E}\{y:H_k(y)=s\}.
\]

## D.2 Collision theorem

Prove

\[
D_k(H_kx)=x
\iff
\ker H_k\cap S_x=\varnothing.
\]

Deduce the exact first successful depth and monotonicity of success under
increasing \(k\).

## D.3 Sharp finite separation

Prove that \(2^k>|S_x|\) guarantees a linear
\(H:\mathbb F_2^n\to\mathbb F_2^k\) with
\(\ker H\cap S_x=\varnothing\), both probabilistically and by lexicographically
first finite matrix search. Deduce the sharper bound

\[
k\le\left\lceil\log_2r_E(x)\right\rceil\le n.
\]

Delete dependent rows without changing the kernel and extend the remaining
ordered rows to a nested full-rank family.

Prove sharpness of the universal depth bound: for every \(d\le n\), construct
an exact energy order and point \(x\) with \(r_E(x)=2^d\) such that every
successful linear map has at least \(d\) rows.

## D.4 Uniform residual families

For every finite \(B\subseteq X\), including \(B=\varnothing\), prove

\[
\text{each kernel coset meets }B\text{ at most once}
\iff
\ker H\cap(B-B)\subseteq\{0\}.
\]

Recover equality when \(B\ne\varnothing\). For integer
\(r\in\{0,\ldots,n\}\), prove

\[
B_r-B_r=B_{\min(2r,n)}
\]

and show that uniqueness on \(B_r\) is equivalent to
\(d_{\min}(\ker H)>2r\), with \(d_{\min}(\{0\})=\infty\). Deduce

\[
2^k\ge|B_r|.
\]

For a finite union \(\bigcup_i(p_i+B_{r_i})\), derive and prove the exact
pairwise translated-ball condition.

## D.5 First-hit certificates

For \(0\le B\le2^n\), let \(y_1,\ldots,y_B\) be the first \(B\) energy-ordered
candidates. The canonical bounded decoder returns the first syndrome match.
For \(1\le j\le B\), prove that

\[
x=y_j,\qquad H(x)=s,\qquad H(y_i)\ne s\ (i<j)
\]

is necessary and sufficient for a first-hit certificate.

The canonical sequential verifier computes \(H(y_1),\ldots,H(y_j)\) in order.
Prove that it uses exactly \(j\) matrix-vector evaluations. Give an explicit
family showing why this is not a lower bound for arbitrary verifiers allowed
to preprocess spans and reuse linear combinations.

---

# Independence and completion

Problems A-D use disjoint definitions and conclusions. A complete solution to
one problem proves every clause in that problem, including its constructions,
sharpness families, edge cases, and certificates. No application consequence
is part of the grading.
