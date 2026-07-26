# The Atlas and Clockwork Mathematical Examination

## Instructions to solvers

This is a pencil-and-paper examination in finite mathematics. It contains four
independent problems. Each problem asks for a theorem, a constructive
mathematical description, and a proof.

No numerical dataset, computer program, experiment, implementation, benchmark,
or machine-generated certificate is part of the examination. A solver may use
ordinary mathematical notation and established theorems, provided every
nonstandard result used is stated precisely.

A complete solution to any one problem is accepted as a complete independent
solution. No problem depends on a definition, lemma, or result from another
problem.

The four subjects are:

1. Prefix-paid information and finite variational duality.
2. Predictive right congruences and Wheeler interval geometry.
3. Integer shadowing of contractive selective recurrences.
4. Unique reconstruction in energy-ordered parity cosets.

All logarithms are base two unless stated otherwise.

---

# Problem A: The Paid-Information Variational Principle

## A.1 Finite paid-information system

Let \(J\) and \(K\) be positive integers. Let

\[
G=(g_{jk})\in\mathbb R^{J\times K}
\]

be an arbitrary finite gain matrix. Entry \(g_{jk}\) is the gain obtained on
block \(j\) when explanation \(k\) is selected before that block is revealed.

A binary prefix code on \(\{1,\ldots,K\}\) is represented by integer lengths

\[
\ell_1,\ldots,\ell_K\in\mathbb N
\]

satisfying Kraft's inequality

\[
\sum_{k=1}^{K}2^{-\ell_k}\le 1.
\]

For a legal length vector \(\ell\), define the paid-information value

\[
V_G(\ell)
=
\sum_{j=1}^{J}
\max_{1\le k\le K}
\left(g_{jk}-\ell_k\right).
\]

Define

\[
V^*(G)
=
\sup_{\ell\in\mathbb N^K:
\sum_k2^{-\ell_k}\le1}
V_G(\ell).
\]

Ties in each row may be resolved arbitrarily. A solution must show that the
value does not depend on tie resolution.

## A.2 Relaxed weights

Let

\[
\Delta_K
=
\left\{
q\in(0,1]^K:
\sum_{k=1}^{K}q_k\le1
\right\}.
\]

Define the relaxed functional

\[
\mathcal V_G(q)
=
\sum_{j=1}^{J}
\max_{1\le k\le K}
\left(g_{jk}+\log q_k\right).
\]

For an assignment

\[
z=(z_1,\\ldots,z_J)
\in\{1,\ldots,K\}^J,
\]

let

\[
n_k(z)=|\{j:z_j=k\}|.
\]

Adopt the convention \(0\log0=0\).

## A.3 Questions

Prove all of the following.

### A1. Exact finite duality

Derive an exact variational formula for

\[
\sup_{q\in\Delta_K}\mathcal V_G(q)
\]

as a maximization over assignments \(z\). The final expression must contain
only the selected gains \(g_{j,z_j}\), the counts \(n_k(z)\), and an explicit
entropy term.

Prove existence of an optimizer and characterize every optimizing weight
vector \(q\), including unused explanations.

### A2. Integer prefix penalty

Prove universal upper and lower bounds relating \(V^*(G)\) to the relaxed
optimum. The gap must be an explicit constant independent of the magnitudes of
the entries of \(G\).

Determine the smallest universal constant that can hold for every \(J,K,G\),
or prove matching lower and upper constants if the exact optimum cannot be
expressed by one constant.

Your proof must construct an actual prefix code from an optimizing relaxed
weight vector.

### A3. Description-priced explanations

Let \(d_1,\ldots,d_K\ge0\) be arbitrary finite description prices and define

\[
V_{G,d}(\ell,z)
=
\sum_{j=1}^{J}
(g_{j,z_j}-\ell_{z_j})
-
\sum_{k:n_k(z)>0}d_k.
\]

Derive a necessary-and-sufficient variational condition for

\[
\max_{\ell,z}V_{G,d}(\ell,z)>D
\]

for an arbitrary real threshold \(D\). The condition may involve a finite
maximization, convex conjugate, or dual measure, but it must not assume the
assignment \(z\) in advance.

### A4. Stability under perturbation

For matrices \(G,G'\) satisfying

\[
\max_{j,k}|g_{jk}-g'_{jk}|\le\varepsilon,
\]

prove the sharpest possible universal bound on

\[
|V^*(G)-V^*(G')|.
\]

Characterize equality cases.

## A.4 Strict solution requirement

A complete solution must provide:

- The exact dual formula.
- A constructive prefix-code argument.
- A complete treatment of zero-count explanations.
- A description-priced threshold theorem.
- A sharp stability theorem.

Numerical optimization of particular matrices is not a solution.

---

# Problem B: The Predictive Wheeler-Quotient Theorem

## B.1 Colored deterministic system

Let \(H\) be a nonempty finite set, let \(A\) be a finite totally ordered
alphabet, and let

\[
T:H\times A\to H
\]

be a total deterministic transition. Let

\[
c:H\to C
\]

be a coloring into a finite set \(C\).

Extend \(T\) to words in \(A^*\) in the usual way. For \(h\in H\) and
\(u=a_1\cdots a_m\in A^*\), define the color trace

\[
\operatorname{Trace}(h,u)
=
\bigl(
 c(h),
 c(T(h,a_1)),
 \ldots,
 c(T(h,a_1\cdots a_m))
\bigr).
\]

Define behavioral equivalence by

\[
h\equiv h'
\quad\Longleftrightarrow\quad
\forall u\in A^*,
\quad
\operatorname{Trace}(h,u)
=
\operatorname{Trace}(h',u).
\]

Let \(Q=H/{\equiv}\), and write \([h]\) for the class of \(h\).

## B.2 Labeled quotient graph

Form a directed labeled multigraph \(G_Q\) with vertex set \(Q\). For every
\(q=[h]\in Q\) and \(a\in A\), include the edge

\[
q\xrightarrow{a}[T(h,a)].
\]

A total order \(<\) on \(Q\) is called Wheeler when:

1. Every indegree-zero vertex precedes every positive-indegree vertex.
2. If \(u\xrightarrow{a}v\) and \(u'\xrightarrow{a'}v'\) with \(a<a'\), then
   \(v<v'\).
3. If the two labels are equal and \(u<u'\), then \(v\le v'\).

For a word \(w\in A^*\), let \(I(w)\subseteq Q\) be the vertices reachable by
a path labeled \(w\).

## B.3 Questions

Prove all of the following.

### B1. Myhill-Nerode characterization

Prove that \(\equiv\) is the unique coarsest equivalence relation on \(H\)
that preserves colors and is a right congruence for \(T\).

Prove that two unequal classes admit a finite distinguishing word. Establish
the best universal upper bound you can on the length of a shortest
distinguishing word in terms of \(|H|\) or \(|Q|\), and determine whether the
bound is sharp.

Give a finite certificate of minimality consisting solely of representatives
and distinguishing words.

### B2. Wheeler interval theorem

Assume \(G_Q\) admits a Wheeler order. Prove that, for every word \(w\), the set
\(I(w)\) is an interval in that order.

Prove a converse under the weakest hypotheses you can identify: if every
nonempty \(I(w)\) is an interval in some total order, when must that order
satisfy the Wheeler axioms?

State every necessary exception explicitly.

### B3. Minimal Wheeler refinement

When \(G_Q\) does not admit a Wheeler order, define a finite refinement of
behavioral classes by splitting classes but never merging behaviorally unequal
states.

Prove or disprove:

> Every finite colored deterministic system has a unique coarsest refinement
> whose quotient graph admits a Wheeler order, up to order-preserving colored
> isomorphism.

If false, characterize the obstruction and define a canonical optimum using a
precise secondary criterion. Prove existence and provide a finite minimality
certificate.

### B4. Continuation multiplicity bound

Suppose the refined Wheeler graph has \(r\) maximal equal-label runs in its
edge sequence under source order. Derive the strongest general bound you can
on the number of distinct continuation intervals

\[
\{I(w):w\in A^*\}
\]

in terms of \(|Q|\), \(|A|\), and \(r\).

Provide examples showing which terms in your bound are necessary.

## B.4 Strict solution requirement

A complete solution must provide:

- The behavioral-equivalence theorem directly from traces.
- Finite distinguishing certificates.
- The Wheeler interval theorem and converse conditions.
- A proved resolution of the minimal-refinement question.
- A continuation-interval bound with extremal examples.

An implementation of automaton minimization or graph indexing is not a
solution.

---

# Problem C: Integer Shadowing of Selective Recurrences

## C.1 Contractive selective system

Let \((V,\|\cdot\|)\) be \(\mathbb R^d\) with a fixed norm. Let \(\mathcal A\)
be a finite alphabet. For every \(a\in\mathcal A\), let

\[
F_a(s)=A_as+b_a,
\]

where \(A_a\in\mathbb Q^{d\times d}\), \(b_a\in\mathbb Q^d\), and

\[
\|A_a\|\le\rho<1.
\]

Given an input sequence \(a_1,\ldots,a_n\), define

\[
s_{t+1}=F_{a_t}(s_t).
\]

Let the output logit be

\[
y_t=c^Ts_t+\gamma_{a_t},
\]

where \(c\in\mathbb Q^d\) and \(\gamma_a\in\mathbb Q\).

For \(x\in\{0,1\}\), define logistic loss

\[
\lambda(x,y)
=
\log_2(1+e^y)-\frac{xy}{\ln2}.
\]

## C.2 Integer shadow system

For integer precision \(m\ge1\), let

\[
\Lambda_m=2^{-m}\mathbb Z^d.
\]

A rounding map \(R_m:\mathbb R^d\to\Lambda_m\) is admissible when

\[
\|R_m(v)-v\|\le\eta_m
\]

for every \(v\), with explicit \(\eta_m\).

Define the integer shadow recurrence

\[
\widehat s_{t+1}
=
R_m(\widehat A_{a_t}\widehat s_t+
\widehat b_{a_t}),
\]

and output

\[
\widehat y_t
=
\widehat c^T\widehat s_t+
\widehat\gamma_{a_t}.
\]

All hatted quantities must be rational with denominator dividing \(2^m\).

## C.3 Questions

Prove all of the following.

### C1. Uniform shadowing

Derive the sharpest uniform upper bound you can for

\[
\sup_{1\le t\le n}\|s_t-\widehat s_t\|
\]

in terms of:

- Initial-state error.
- \(\rho\).
- Matrix approximation errors.
- Bias approximation errors.
- Rounding error \(\eta_m\).
- A bound on the exact and shadow states.

Your theorem must hold uniformly over every input sequence and every length
\(n\).

### C2. Cumulative logistic-loss transfer

Prove an explicit bound on

\[
\sum_{t=1}^{n}
\left(
\lambda(x_t,\widehat y_t)
-
\lambda(x_t,y_t)
\right)
\]

that holds for every binary outcome sequence \(x_1,\ldots,x_n\).

Determine the sharp Lipschitz constant of logistic loss with respect to the
logit under base-two measurement, and propagate every approximation term
explicitly.

### C3. Householder realization

For a rational matrix \(A\) with \(\|A\|<1\), study representations of the
form

\[
A
=
D
\prod_{j=1}^{k}
\left(
I-2\frac{v_jv_j^T}{v_j^Tv_j}
\right)
+E,
\]

where \(D\) is diagonal, the \(v_j\) are rational, and \(E\) is sparse.

Derive sufficient conditions and explicit bounds on \(k\), the sparsity of
\(E\), and coefficient denominators guaranteeing operator error at most
\(\delta\).

Determine which classes of contractive matrices admit exact representation
with \(E=0\), and prove your characterization.

### C4. Precision threshold

Given a prescribed total allowance \(\varepsilon>0\), derive a constructive
inequality on \(m,k,\delta\), and the coefficient approximations sufficient to
guarantee cumulative excess logistic loss at most \(\varepsilon\) for every
sequence of length \(n\).

The result must state all dependence on \(n,d,\rho,c\), and the state bound.

## C.4 Strict solution requirement

A complete solution must provide:

- A uniform integer-shadowing theorem.
- A cumulative logistic-loss theorem.
- A rational Householder-plus-sparse approximation theorem.
- An explicit precision threshold.
- Sharpness examples or lower bounds for the principal terms.

Numerical simulation of selected recurrences is not a solution.

---

# Problem D: Energy-Ordered Parity Reconstruction

## D.1 Ordered finite space

Let \(X=\mathbb F_2^n\). Let

\[
E:X\to\mathbb R
\]

be an arbitrary energy function, and let \(\prec_E\) be the total order obtained
by increasing energy with lexicographic tie breaking.

For \(x\in X\), define its energy rank

\[
r_E(x)
=
1+|\{y\in X:y\prec_E x\}|.
\]

Let

\[
H_k:X\to\mathbb F_2^k
\]

be a nested family of linear maps: the first \(k
	ext{ rows of }H_{k+1}\)
coincide with \(H_k\).

For syndrome \(s\in\mathbb F_2^k\), define the ideal reconstruction

\[
D_k(s)
=
\min_{\prec_E}\{y:H_k(y)=s\}.
\]

## D.2 Questions

Prove all of the following.

### D1. Exact collision characterization

Prove a necessary-and-sufficient condition for

\[
D_k(H_kx)=x
\]

expressed solely in terms of the vectors preceding \(x\) under \(\prec_E\) and
the kernel of \(H_k\).

Derive the sharpest general relationship possible among minimum successful
\(k\), energy rank, and the collision structure of the nested family.

### D2. Universal nested families

Determine whether there exists a deterministic nested family \((H_k)\),
independent of \(E\), with a universal constant \(c\) such that for every
energy order and every \(x\),

\[
D_k(H_kx)=x
\]

for some

\[
k\le\lceil\log_2r_E(x)\rceil+c.
\]

Prove existence with the smallest possible \(c\), or prove impossibility and
give the strongest replacement theorem.

### D3. Structured residual balls

Let \(p\in X\) be a prototype and suppose energy is monotone in a weighted
edit measure around \(p\). Characterize linear maps for which every coset
intersects the radius-\(r\) residual ball in at most one point.

Relate the minimum number of parity rows to the cardinality and additive
structure of the residual ball. Give matching constructions and obstructions
for at least Hamming balls and disjoint weighted edit families.

### D4. Bounded-search certificate

Let \(S\subseteq X\) be a finite candidate set listed in energy order. Define a
bounded decoder that searches exactly the first \(B\) candidates.

Give a finite certificate, verifiable by ordinary mathematical reasoning, that
proves a transmitted syndrome uniquely identifies \(x\) within this bounded
search. Determine the minimum information such a certificate must contain in
the worst case without simply listing all rejected candidates.

## D.3 Strict solution requirement

A complete solution must provide:

- The exact collision theorem.
- A resolution of the universal-family question.
- Prototype-residual uniqueness theorems.
- A bounded-search uniqueness certificate.
- Extremal examples proving sharpness or impossibility where claimed.

A parity-search implementation or empirical collision table is not a solution.

---

# Final independence rule

The four problems are logically independent:

- Problem A concerns finite variational coding under Kraft's inequality.
- Problem B concerns behavioral quotients and ordered graph geometry.
- Problem C concerns shadowing and rational matrix approximation.
- Problem D concerns linear cosets and energy order.

A solution to one problem may use standard published mathematics but may not
assume a result requested by another problem in this examination.

The solver submits only a mathematical manuscript containing definitions,
lemmas, constructions, proofs, and counterexamples. No other artifact is
required.
