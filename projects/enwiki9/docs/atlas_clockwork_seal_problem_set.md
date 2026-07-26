# The Atlas and Clockwork Mathematical Examination

Distribution status: `DRAFT - EXPERT REVIEW ONLY`
Problem version: `ACS-MATH-DRAFT-2-WORKING`

This document is a problem bank, not an authorized candidate examination.
`ACS-MATH-SEAL-2` is `UNBOUND`, and no route is authorized for solver
distribution. This notice may be removed only after the committed Seal
verifier reports `VALID_BOUND`.

This working draft incorporates the C1, D3, and D4 corrections discovered in
the recorded solutions to `ACS-MATH-DRAFT-1`. It is not frozen for a solver
submission until its exact hash is entered in the version ledger.

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

Let \(J\) and \(K\) be positive integers and let

\[
G=(g_{jk})\in\mathbb R^{J\times K}.
\]

Entry \(g_{jk}\) is the gain on block \(j\) when explanation \(k\) is selected
before that block is revealed.

A binary prefix code on an active subset of \(\{1,\ldots,K\}\) is represented
by extended integer lengths

\[
\ell_k\in\overline{\mathbb N}:=\mathbb Z_{\ge0}\cup\{\infty\}.
\]

Use \(2^{-\infty}=0\) and \(x-\infty=-\infty\). At least one length is
finite, and

\[
\sum_{k=1}^{K}2^{-\ell_k}\le1.
\]

A zero-length codeword is allowed exactly when it is the only active codeword.
Inactive explanations have length \(\infty\). Define

\[
V_G(\ell)=\sum_{j=1}^{J}\max_k(g_{jk}-\ell_k)
\]

and

\[
V^*(G)=
\sup_{\ell\in\overline{\mathbb N}^K:\,\sum_k2^{-\ell_k}\le1}
V_G(\ell).
\]

Ties in a row may be resolved arbitrarily; prove that the value is independent
of tie resolution.

## A.2 Relaxed weights

Let

\[
\Delta_K=\left\{q\in[0,1]^K:\sum_{k=1}^{K}q_k\le1\right\}.
\]

Use \(\log0=-\infty\), and define
\(\mathcal V_G(0,\ldots,0)=-\infty\). For every other \(q\in\Delta_K\), let

\[
\mathcal V_G(q)=
\sum_{j=1}^{J}\max_k(g_{jk}+\log q_k).
\]

For an assignment \(z=(z_1,\ldots,z_J)\in\{1,\ldots,K\}^J\), define

\[
n_k(z)=|\{j:z_j=k\}|,
\]

and use \(0\log0=0\).

## A.3 Questions

Prove all of the following.

### A1. Exact finite duality

Prove

\[
\max_{q\in\Delta_K}\mathcal V_G(q)
=
\max_{z\in\{1,\ldots,K\}^J}
\left[
\sum_{j=1}^{J}g_{j,z_j}
+
\sum_{k:n_k(z)>0}n_k(z)\log\frac{n_k(z)}J
\right].
\]

Prove existence of an optimizer. Prove that \(q\) is optimizing if and only if
there is an optimizing assignment \(z\), selected from the rowwise maximizers
at \(q\), such that

\[
q_k=\frac{n_k(z)}J
\]

for every \(k\). In particular, characterize all zero-count explanations.

### A2. Integer prefix penalty

Writing

\[
\mathcal V^*(G)=\max_{q\in\Delta_K}\mathcal V_G(q),
\]

prove

\[
\mathcal V^*(G)-J\le V^*(G)\le\mathcal V^*(G).
\]

Construct an actual binary prefix code from an optimizing relaxed weight vector.
Zero weights must remain inactive rather than receiving finite codewords.

### A3. Description-priced explanations

Let \(d_1,\ldots,d_K\ge0\). For a legal \(\ell\) and an assignment using only
finite-length explanations, define

\[
V_{G,d}(\ell,z)
=
\sum_{j=1}^{J}(g_{j,z_j}-\ell_{z_j})
-
\sum_{k:n_k(z)>0}d_k.
\]

For \(n\in\mathbb Z_{\ge0}^K\) with \(\sum_kn_k=J\), define the exact finite
prefix price

\[
L(n)=
\min_{\ell:\,\sum_k2^{-\ell_k}\le1}
\sum_{k:n_k>0}n_k\ell_k,
\]

where coordinates with \(n_k=0\) may be set to \(\infty\). Prove the exact
necessary-and-sufficient condition

\[
\max_{z\in\{1,\ldots,K\}^J}
\left[
\sum_jg_{j,z_j}
-L(n(z))
-\sum_{k:n_k(z)>0}d_k
\right]>D
\]

for \(\max_{\ell,z}V_{G,d}(\ell,z)>D\). Prove that the minimum defining
\(L(n)\) exists and give a finite constructive procedure for obtaining it.

### A4. Stability under perturbation

If

\[
\max_{j,k}|g_{jk}-g'_{jk}|\le\varepsilon,
\]

prove

\[
|V^*(G)-V^*(G')|\le J\varepsilon.
\]

Prove that the coefficient \(J\) is optimal by giving equality cases.

## A.4 Strict solution requirement

A complete solution must provide:

- The stated exact dual formula and optimizer characterization.
- The constructive prefix-code argument and zero-weight treatment.
- The exact description-priced threshold theorem.
- The sharp stated stability theorem.

Numerical optimization of particular matrices is not a solution.

---

# Problem B: The Predictive Wheeler-Quotient Theorem

## B.1 Colored deterministic system

Let \(H\) be a nonempty finite set, \(A\) a finite totally ordered alphabet,
\(T:H\times A\to H\) a total deterministic transition, and \(c:H\to C\) a
finite coloring. Extend \(T\) to words. For
\(u=a_1\cdots a_m\), define

\[
\operatorname{Trace}(h,u)=
\bigl(c(h),c(T(h,a_1)),\ldots,c(T(h,a_1\cdots a_m))\bigr).
\]

Define

\[
h\equiv h'
\quad\Longleftrightarrow\quad
\forall u\in A^*,\quad
\operatorname{Trace}(h,u)=\operatorname{Trace}(h',u).
\]

Let \(Q=H/{\equiv}\), and write \([h]\) for the class of \(h\).

## B.2 Labeled quotient graph

Form the directed labeled multigraph \(G_Q\) with vertex set \(Q\) and edges

\[
[h]\xrightarrow{a}[T(h,a)].
\]

A total order \(<\) on \(Q\) is Wheeler when:

1. Every indegree-zero vertex precedes every positive-indegree vertex.
2. If \(u\xrightarrow{a}v\) and \(u'\xrightarrow{a'}v'\) with \(a<a'\), then
   \(v<v'\).
3. If labels are equal and \(u<u'\), then \(v\le v'\).

For \(w\in A^*\), let \(I(w)\subseteq Q\) be the vertices reachable by a path
labeled \(w\).

## B.3 Questions

Prove all of the following.

### B1. Myhill-Nerode characterization

Prove that \(\equiv\) is the unique coarsest color-preserving right congruence
for \(T\). Prove that two unequal classes admit a finite distinguishing word.
If \(|Q|\ge2\), prove that a shortest distinguishing word has length at most
\(|Q|-2\), and construct a family attaining this bound.

Give a finite minimality certificate containing one representative per class
and one distinguishing word for each unordered pair of representatives.

### B2. Wheeler interval theorem

Prove the following equivalence for a total order \(<\) on \(Q\):

1. The order is Wheeler.
2. Indegree-zero vertices come first; each \(I(a)\), \(a\in A\), is an
   interval; for all \(a<a'\) with \(I(a),I(a')\ne\varnothing\),
   \[
   \max I(a)<\min I(a');
   \]
   and
   \(q\mapsto T(q,a)\) is nondecreasing for every fixed \(a\).

Under either condition, prove by induction that every \(I(w)\) is an interval.

### B3. Canonical finite Wheeler unfolding

Fix \(L\ge0\). Define the depth-\(L\) path unfolding with vertices

\[
(q,w)\in Q\times A^{\le L},
\]

tagged by terminal class \(T(q,w)\), and edges

\[
(q,w)\xrightarrow{a}(q,wa)
\qquad(|w|<L).
\]

Order vertices first by colexicographic order of \(w\), then by a fixed order of
\(q\). Prove that this unfolding is Wheeler, never merges behaviorally unequal
terminal classes, and has exactly

\[
|Q|\sum_{i=0}^{L}|A|^i
\quad\text{vertices and}\quad
|Q|\sum_{i=1}^{L}|A|^i
\quad\text{edges}.
\]

Prove that every represented continuation of length at most \(L\) occupies one
interval. Give a finite certificate consisting of the ordered vertex list,
terminal-class tags, and edge list.

### B4. Continuation multiplicity bound

Let \(n_Q=|Q|\). Prove

\[
\left|\{I(w):w\in A^*\}\right|
\le
1+\frac{n_Q(n_Q+1)}2.
\]

The extra one accounts for the empty set. Construct Wheeler systems with at
least \(n_Q\) distinct continuation intervals, proving that no bound independent
of \(n_Q\) is possible.

## B.4 Strict solution requirement

A complete solution must provide:

- The behavioral-equivalence theorem and sharp distinguishing-word bound.
- Finite distinguishing certificates.
- The stated Wheeler equivalence and interval theorem.
- The depth-\(L\) Wheeler unfolding and exact size certificate.
- The stated continuation-interval bound and lower-bound family.

An implementation of automaton minimization or graph indexing is not a
solution.

---

# Problem C: Integer Shadowing of Selective Recurrences

## C.1 Contractive selective system

Let \(V=\mathbb R^d\) with Euclidean norm \(\|\cdot\|_2\), using its induced
operator norm for matrices. Let \(\mathcal A\) be a finite alphabet. For every
\(a\in\mathcal A\), let

\[
F_a(s)=A_as+b_a,
\]

where \(A_a\in\mathbb Q^{d\times d}\), \(b_a\in\mathbb Q^d\), and

\[
\|A_a\|_2\le\rho<1.
\]

For an input \(a_1,\ldots,a_n\), define

\[
s_{t+1}=F_{a_t}(s_t),
\qquad
y_t=c^Ts_t+\gamma_{a_t},
\]

where \(c\in\mathbb Q^d\) and \(\gamma_a\in\mathbb Q\). For
\(x\in\{0,1\}\), define

\[
\lambda(x,y)=\log_2(1+e^y)-\frac{xy}{\ln2}.
\]

## C.2 Integer shadow system

For \(m\ge1\), let \(\Lambda_m=2^{-m}\mathbb Z^d\). Let \(R_m\) round each
coordinate to the nearest lattice point with a fixed tie rule. Prove and use

\[
\|R_m(v)-v\|_2\le\eta_m:=\sqrt d\,2^{-m-1}.
\]

Define

\[
\widehat s_{t+1}
=
R_m(\widehat A_{a_t}\widehat s_t+\widehat b_{a_t}),
\qquad
\widehat y_t
=
\widehat c^T\widehat s_t+\widehat\gamma_{a_t}.
\]

The stored recurrent coefficients
\(\widehat A_a,\widehat b_a,\widehat c,\widehat\gamma_a\) and every stored state
\(\widehat s_t\) are dyadic with denominator dividing \(2^m\). Matrix-vector
products may use exact widened rational intermediates, but \(R_m\) is applied
before the next state is stored.

## C.3 Questions

Prove all of the following.

### C1. Uniform shadowing

Assume

\[
\|s_t\|_2,\|\widehat s_t\|_2\le S,
\quad
\|A_a-\widehat A_a\|_2\le\varepsilon_A,
\quad
\|b_a-\widehat b_a\|_2\le\varepsilon_b.
\]

Writing \(e_t=\|s_t-\widehat s_t\|_2\), prove for every input sequence

\[
e_t
\le
\rho^{t-1}e_1
+
\frac{1-\rho^{t-1}}{1-\rho}
(\varepsilon_A S+\varepsilon_b+\eta_m).
\]

Prove exact one-dimensional attainment of the coefficients of \(e_1\) and of
the accumulated one-step error whenever \(\rho\) is attainable by the permitted
rational coefficient class. For every real \(\rho\in[0,1)\), prove that the
same coefficients are sharp as suprema over admissible rational scalar
contraction factors tending upward to \(\rho\).

### C2. Cumulative logistic-loss transfer

Assume

\[
\|c-\widehat c\|_2\le\varepsilon_c,
\qquad
|\gamma_a-\widehat\gamma_a|\le\varepsilon_\gamma.
\]

Prove that the sharp global Lipschitz constant of \(\lambda(x,\cdot)\), uniformly
in \(x\in\{0,1\}\), is \(1/\ln2\). Then prove, for every binary outcome
sequence,

\[
\sum_{t=1}^{n}
[\lambda(x_t,\widehat y_t)-\lambda(x_t,y_t)]
\le
\frac1{\ln2}
\sum_{t=1}^{n}
(\varepsilon_cS+\|c\|_2e_t+\varepsilon_\gamma).
\]

Substitute C1 and simplify the geometric sums into a closed form.

### C3. Householder realization

Suppose a rational matrix is supplied with the exact factorization

\[
A=D\prod_{j=1}^{k}H_j+E,
\qquad
H_j=I-2\frac{v_jv_j^T}{v_j^Tv_j},
\]

where \(D\) is diagonal, every nonzero \(v_j\) is rational, and \(E\) is
sparse. Suppose

\[
\|\widehat D-D\|_2\le\varepsilon_D,
\quad
\|\widehat H_j-H_j\|_2\le\varepsilon_H,
\quad
\|\widehat E-E\|_2\le\varepsilon_E,
\quad
\|D\|_2\le d_0.
\]

Define the exact widened intermediate and its stored dyadic realization by

\[
\widetilde A
=
\widehat D\prod_{j=1}^{k}\widehat H_j+\widehat E,
\qquad
\widehat A=Q_m(\widetilde A),
\]

where \(Q_m\) rounds every entry to the nearest multiple of \(2^{-m}\) under a
fixed tie rule. Prove

\[
\|Q_m(M)-M\|_2
\le
\eta_{A,m}:=d\,2^{-m-1}
\]

for every \(d\times d\) matrix \(M\), and prove

\[
\|\widehat A-A\|_2
\le
\varepsilon_D(1+\varepsilon_H)^k
+d_0[(1+\varepsilon_H)^k-1]
+\varepsilon_E
+\eta_{A,m}.
\]

Also prove that every rational orthogonal \(d\times d\) matrix is a product of
at most \(d\) rational Householder reflections.

### C4. Precision threshold

Let \(\delta_A\) be the complete C3 error, including
\(\eta_{A,m}\), and define

\[
\varepsilon_{\rm step}=\delta_AS+\varepsilon_b+\eta_m.
\]

Prove that

\[
\frac n{\ln2}
\left[
\varepsilon_cS+\varepsilon_\gamma
+\|c\|_2
\left(e_1+\frac{\varepsilon_{\rm step}}{1-\rho}\right)
\right]
\le\varepsilon
\]

is sufficient for cumulative excess logistic loss at most \(\varepsilon\) on
every sequence of length \(n\). Substitute the C3 expression for \(\delta_A\).
For nearest dyadic scalar rounding, state and prove explicit dimension-dependent
bounds in \(m\) for vector and matrix approximation errors, and substitute them
to obtain a fully explicit sufficient lower bound on \(m\).

## C.4 Strict solution requirement

A complete solution must provide:

- The stated uniform integer-shadowing theorem and sharpness construction.
- The sharp logistic Lipschitz constant and cumulative-loss theorem.
- The stated Householder perturbation inequality.
- The rational-orthogonal factorization theorem.
- The stated explicit precision threshold.

Numerical simulation of selected recurrences is not a solution.

---

# Problem D: Energy-Ordered Parity Reconstruction

## D.1 Ordered finite space

Let \(X=\mathbb F_2^n\). Let \(E:X\to\mathbb R\), and let \(\prec_E\) be the
total order obtained by increasing energy with lexicographic tie breaking. For
\(x\in X\), define

\[
r_E(x)=1+|\{y\in X:y\prec_E x\}|.
\]

For \(0\le k\le n\), let \(H_k:X\to\mathbb F_2^k\) be a nested family of
linear maps: \(H_0\) is the zero-row map, the first \(k\) rows of \(H_{k+1}\)
coincide with \(H_k\), and \(H_n\) has rank \(n\). For
\(s\in\mathbb F_2^k\), define

\[
D_k(s)=\min_{\prec_E}\{y:H_k(y)=s\}.
\]

## D.2 Questions

Prove all of the following.

### D1. Exact collision characterization

Prove

\[
D_k(H_kx)=x
\quad\Longleftrightarrow\quad
\ker H_k\cap\{y+x:y\prec_E x\}=\varnothing.
\]

Deduce that the minimum successful depth in a fixed nested family is exactly

\[
\min\{k:\ker H_k\cap\{y+x:y\prec_E x\}=\varnothing\}.
\]

### D2. Finite separating maps

For fixed \(E\) and \(x\), put

\[
S_x=\{y+x:y\prec_E x\}.
\]

Prove that whenever \(2^k>|S_x|\), there exists a linear map
\(H:\mathbb F_2^n\to\mathbb F_2^k\) with
\(\ker H\cap S_x=\varnothing\). Conclude that one may choose

\[
k\le\min\{n,\lceil\log_2r_E(x)\rceil+1\}
\]

and recover \(x\) exactly. Give both a probabilistic proof and a deterministic
finite construction by choosing the lexicographically first successful matrix.
Show how to delete dependent rows and extend its ordered rows to a nested
full-rank family.

### D3. Structured residual sets

For an arbitrary finite \(B\subseteq\mathbb F_2^n\), including
\(B=\varnothing\), prove that every coset of \(\ker H\) meets \(B\) in at most
one point if and only if

\[
\ker H\cap(B-B)\subseteq\{0\}.
\]

Prove that when \(B\ne\varnothing\), the inclusion is equivalent to

\[
\ker H\cap(B-B)=\{0\}.
\]

Apply this theorem to the Hamming ball \(B_r\), using
\(B_r-B_r=B_{\min(2r,n)}\). Prove that uniqueness is equivalent to the kernel
code having minimum distance greater than \(2r\), with the zero code assigned
infinite minimum distance, and derive

\[
2^k\ge|B_r|.
\]

For

\[
B=\bigcup_{i=1}^{m}(p_i+B_{r_i}),
\]

write and prove the exact pairwise-difference condition on \(\ker H\) that is
necessary and sufficient for unique coset intersection.

### D4. Bounded-search first-hit certificate

Let \(S_B=(y_1,\ldots,y_B)\) be the first \(B\) candidates in energy order.
Define the bounded decoder to return the first \(y_i\) satisfying \(H(y_i)=s\),
or `FAIL` if none exists.

Assume a verifier is given \(H\), \(s\), \(S_B\), and a claimed pair \((j,x)\).
Prove that the pair is a valid finite first-hit certificate if and only if

\[
x=y_j,
\qquad H(x)=s,
\qquad H(y_i)\ne s\quad(1\le i<j).
\]

Prove that these checks are necessary and sufficient for the bounded decoder to
return \(x\). Define the canonical sequential verifier to evaluate
\(H(y_1),\ldots,H(y_j)\) in order, stopping at the claimed first hit. Prove
that this verifier performs exactly \(j\) matrix-vector evaluations on a valid
certificate. Do not claim this count as a lower bound for arbitrary verifiers
that may preprocess the candidate span or reuse linear dependencies.

## D.3 Strict solution requirement

A complete solution must provide:

- The exact collision theorem and successful-depth expression.
- The separating-map theorem, both existence proofs, and nested extension.
- The exact difference-set theorem and its stated applications.
- The bounded-search first-hit theorem and the exact canonical sequential
  verification cost.

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
