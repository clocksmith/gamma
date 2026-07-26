# The Independent Finite Prediction Olympiad

## Public statement

This examination contains five independent constructive problems over one
finite binary object. Each problem is a complete alternative route. A solution
to any one problem passes the examination.

The acceptance rule is

\[
\boxed{
\operatorname{PASS}_A
\lor \operatorname{PASS}_B
\lor \operatorname{PASS}_C
\lor \operatorname{PASS}_D
\lor \operatorname{PASS}_E.
}
\]

No problem may use another problem's solution, certificate, labels, state,
tables, savings, proof, or acceptance result.

Contestants submit finite mathematical objects and proofs. They do not submit
executables. Canonical serialization, exact coding, runtime evaluation,
reversibility, and acceptance are controlled by the separately versioned
`Atlas-Clockwork Seal Specification`.

An asymptotic existence theorem, probabilistic construction without a fixed
realization, floating-point experiment, or uncharged oracle is not a solution.

---

# I. Common finite instance

## 1. Construction object

The organizer supplies a finite binary object

\[
x=x_1x_2\cdots x_n,
\qquad x_t\in\{0,1\},
\]

and a partition

\[
0=b_0<b_1<\cdots<b_N=n.
\]

Block \(I_j\) is

\[
I_j=\{b_{j-1}+1,\ldots,b_j\}.
\]

The complete object is available to contestants while constructing their
finite mathematical submission. It is not available to the runtime
interpreter while reconstructing the object.

## 2. Runtime instances

The organizer supplies one common frozen Seal object \(S_{\mathrm{common}}\)
and five disjoint frozen runtime objects

\[
R_A,R_B,R_C,R_D,R_E.
\]

The common object contains only route-neutral grammar, serialization, and coder
definitions. Runtime object \(R_i\) contains only route \(i\)'s fixed constants,
causal observable generators, interpreter adapter, target, and resource bounds.
Its complete reachable dependency closure is frozen, hashed, and charged to
route \(i\).

No runtime object contains \(x\), a future-symbol table, an uncharged
prediction trace, another route's fixed object, or any equivalent encoding of
the construction object.

Before reconstructing position \(t\) on route \(i\), the interpreter may
calculate

\[
\omega_{i,t}=\Omega_i(S_{\mathrm{common}},R_i,x_{<t},\zeta_{\le t}),
\]

where \(\zeta_{\le t}\) denotes only paid auxiliary information whose release
time has arrived. The complete output and state of \(\Omega\) must be
determined by this expression.

A submitted mathematical object may inspect all of \(x\) during construction,
but every surviving instance-dependent bit used during reconstruction must be
serialized and charged by the Seal.

## 3. Common coding and accounting

Every route uses the fixed finite-state dyadic arithmetic coder and the
canonical channels defined by the Seal:

```text
F  framing and lengths
C  decoder-required finite certificate
Z  paid labels, selectors, or auxiliary choices
Y  coded data payload
P  verifier-only proof, unavailable during reconstruction
```

Only `F`, `C`, `Z`, and `Y` contribute variable coded length. `P` is required
for mathematical verification but cannot be read by the runtime interpreter.

For route \(i\), the exact total is

\[
L_i
=
L_{\mathrm{fixed},i}
+8|F_i|
+8|C_i|
+8|Z_i|
+|Y_i|.
\]

Every route has an absolute bit target \(T_i\). It passes its length gate only
if

\[
\boxed{L_i\le T_i.}
\]

Every route also has finite certificate, state, operation, memory, and physical
execution bounds. The full definitions are owned by the Seal.

## 4. Independence

The five problems share only \(x\), the block boundaries, and
\(S_{\mathrm{common}}\). Each route has a separate \(R_i\), namespace,
serializer adapter, fixed-cost ledger, target, interpreter entry point, and
verdict.

A verifier evaluating one route must not load any submitted artifact from
another route or any fixed object outside the transitive dependency closure of
that route's \(R_i\).

---

# Problem A: Paid Partition Martingale

## A.1 Objective

Construct a finite predictive measure that purchases block-level information
through explicitly charged labels and uses it to reduce the complete exact
length below the absolute target.

## A.2 Supplied data

Problem A supplies:

- A finite dyadic probability denominator \(2^r\).
- Causal observable alphabets \(\mathcal O_A\).
- A block-label release schedule.
- Bounds \(B_{A,C},B_{A,Z},B_{A,S},B_{A,O},B_{A,M}\).
- An absolute target \(T_A\).
- A baseline payload for diagnostic comparison only.

The baseline is not available as an uncharged prediction trace during runtime.
Any baseline coordinate exposed to a submitted construction is generated
causally by the fixed runtime object.

## A.3 Required construction

Construct the finite tuple

\[
\mathcal A=(\mathcal Z,\kappa,S,s_1,\Phi,G).
\]

It consists of:

1. A finite label alphabet \(\mathcal Z\), possibly a singleton.
2. A prefix-free binary code \(\kappa:\mathcal Z\to\{0,1\}^*\).
3. One label \(z_j\in\mathcal Z\) for every block.
4. A finite predictive state set \(S\).
5. An explicit initial state \(s_1\in S\).
6. A deterministic transition
   \[
   \Phi:S\times\mathcal O_A\times\mathcal Z\times\{0,1\}\to S.
   \]
7. A deterministic numerator map
   \[
   G:S\times\mathcal O_A\times\mathcal Z
   \to\{1,\ldots,2^r-1\}.
   \]

The constructor may choose \(z_j\) after inspecting the complete block. The
interpreter consumes and releases \(\kappa(z_j)\) at the declared block release
point before any probability may depend on \(z_j\). Future labels remain
logically unavailable even if their serialized bits occur later in `Z`.

At position \(t\in I_j\), define

\[
a_t=G(s_t,\omega_t,z_j),
\]

then, only after reconstructing \(x_t\), update

\[
s_{t+1}=\Phi(s_t,\omega_t,z_j,x_t).
\]

## A.4 Submitted objects

Submit:

- The finite label alphabet and code.
- The complete label sequence.
- The state representation.
- The transition and numerator maps.
- Every table, constant, exception, and initializer.
- A proof of prefix-free decoding.
- A proof of causality and state closure.
- A joint encoder-decoder recurrence proof.
- Exact channel and resource ledgers.
- A proof that \(L_A\le T_A\).

## A.5 Pass condition

Problem A passes exactly when the Seal verifies

\[
L_A\le T_A,
\]

\[
|C_A|\le B_{A,C},
\qquad
|Z_A|\le B_{A,Z},
\]

\[
|S|\le B_{A,S},
\qquad
\operatorname{Ops}_A\le B_{A,O},
\qquad
\operatorname{Mem}_A\le B_{A,M},
\]

plus exact reconstruction, deterministic replay, canonical re-encoding, and
the physical execution gate.

A valid Problem A solution is complete and uses no result from Problems B, C,
D, or E.

---

# Problem B: Minimal Predictive Right Quotient

## B.1 Objective

Construct the unique coarsest predictive right congruence of a supplied finite
causal history automaton, realize its quotient recurrence, and meet the
absolute target without paid labels.

## B.2 Supplied finite history system

Problem B supplies, inside its construction data:

1. A finite history-state set \(H_B\).
2. An initial history state \(h_1\in H_B\).
3. A finite descriptor alphabet \(\mathcal D_B\).
4. A causal runtime descriptor generator
   \[
   d_t=\Delta_B(S_{\mathrm{common}},R_B,x_{<t}).
   \]
5. A total deterministic history transition
   \[
   T_B:H_B\times\mathcal D_B\times\{0,1\}\to H_B.
   \]
6. A finite predictive-color map
   \[
   \chi_B:H_B\times\mathcal D_B\to\mathcal K_B.
   \]
7. A dyadic numerator assigned to every color
   \[
   \alpha_B:\mathcal K_B\to\{1,\ldots,2^r-1\}.
   \]
8. Bounds \(B_{B,C},B_{B,Q},B_{B,O},B_{B,M}\).
9. An absolute target \(T_B\).

The fixed runtime object \(R_B\) contains the finite history transition and
causal descriptor generator only when their complete fixed costs are charged
to \(L_{\mathrm{fixed},B}\). Predictive colors may be used offline to define
the quotient but are not runtime advice unless their required representation
is included in \(R_B\) or `C_B`.

No label or selector channel is supplied. Thus \(Z_B\) is empty.

## B.3 Predictive right congruence

An equivalence relation \(\sim\) on \(H_B\) is admissible exactly when, for all
\(h,h'\in H_B\), \(d\in\mathcal D_B\), and \(b\in\{0,1\}\),

\[
h\sim h'
\Longrightarrow
\chi_B(h,d)=\chi_B(h',d),
\]

and

\[
h\sim h'
\Longrightarrow
T_B(h,d,b)\sim T_B(h',d,b).
\]

Thus equivalent histories have identical predictive colors for every
descriptor and remain equivalent after every equal continuation symbol.

Among all admissible equivalence relations, let \(\sim_B^\star\) be the
coarsest one, meaning every other admissible relation refines it. Because
\(H_B\) is finite and admissibility is closed under intersection of
distinguishability refinements, this relation is uniquely defined.

## B.4 Required construction

Construct

\[
\mathcal Q=(Q,\pi,q_1,\delta,\nu,\mathcal W),
\]

where:

1. \(\pi:H_B\twoheadrightarrow Q\) is a surjection satisfying
   \[
   \pi(h)=\pi(h')\Longleftrightarrow h\sim_B^\star h'.
   \]
2. \(q_1=\pi(h_1)\).
3. The induced transition is
   \[
   \delta(\pi(h),d,b)=\pi(T_B(h,d,b)).
   \]
4. The induced numerator is
   \[
   \nu(\pi(h),d)=\alpha_B(\chi_B(h,d)).
   \]
5. \(\mathcal W\) is a finite minimality witness.

No exceptional congruence violations are permitted. A history requiring
different behavior must belong to a refined quotient state.

The witness \(\mathcal W\) must give, for every pair of distinct quotient
states, either an immediate predictive-color distinction or a finite
descriptor-and-bit continuation whose first distinction proves the pair
cannot be merged by any admissible right congruence.

At runtime, the interpreter tracks only \(q_t\). It uses

\[
a_t=\nu(q_t,d_t),
\]

then updates

\[
q_{t+1}=\delta(q_t,d_t,x_t).
\]

It does not consult \(\pi\), \(\chi_B\), or the construction history state
unless their runtime representations are explicitly fixed and charged.

## B.5 Mathematical proof obligations

Prove:

- The descriptor generator is causal.
- \(\pi\) is a total surjection.
- Its fibers form an equivalence relation.
- Predictive-color equality holds within every fiber.
- \(\delta\) and \(\nu\) are well defined, independent of representative.
- The quotient is a right congruence.
- Every pair of quotient states has a valid distinguishing witness.
- The witness proves coarseness and therefore minimal quotient cardinality.
- Runtime recurrence uses no hidden history-specific exception.
- Exact coding and resource inequalities hold.

An empirical clustering, approximate state similarity, ordinary transducer
without \(\pi\), or nonconstructive assertion of minimality is not a solution.

## B.6 Pass condition

Problem B passes exactly when

\[
L_B\le T_B,
\]

\[
|C_B|\le B_{B,C},
\qquad
|Q|\le B_{B,Q},
\]

\[
\operatorname{Ops}_B\le B_{B,O},
\qquad
\operatorname{Mem}_B\le B_{B,M},
\]

and every common Seal gate passes.

A valid Problem B solution is complete and uses no result from Problems A, C,
D, or E.

---

# Problem C: Wheeler Continuation Geometry

## C.1 Objective

Construct a bounded causal Wheeler graph over completed event history, perform
exact rank/select backward search, retrieve only earlier continuations, and
convert those continuations into an exact probability measure under the
absolute target.

## C.2 Supplied data

Problem C supplies:

- A totally ordered finite event alphabet \((\mathcal E_C,\prec)\).
- A causal event generator from reconstructed prefixes.
- A canonical online graph-construction interface.
- Canonical bitvector `rank` and `select` semantics.
- Four organizer-frozen diagnostic control adapters.
- A finite dyadic probability denominator \(2^r\).
- Bounds \(B_{C,C},B_{C,I},B_{C,O},B_{C,M}\).
- An absolute target \(T_C\).

No future graph, suffix array, occurrence list, target-position table, or
offline continuation trace is available at runtime. Every index state must be
rebuilt from completed reconstructed events.

## C.3 Wheeler graph

At event time \(t\), the submitted online builder defines a finite
edge-labeled directed graph

\[
\mathcal G_t=(V_t,E_t,\lambda_t,<_{t}),
\]

where \(\lambda_t:E_t\to\mathcal E_C\) and \(<_{t}\) is a total order on
\(V_t\).

The graph is Wheeler exactly when:

1. Every indegree-zero node precedes every positive-indegree node.
2. For edges \((u,v)\) and \((u',v')\), if
   \[
   \lambda(u,v)\prec\lambda(u',v'),
   \]
   then
   \[
   v<_{t}v'.
   \]
3. If the edge labels are equal and \(u<_{t}u'\), then
   \[
   v\le_t v'.
   \]

The submitted builder must preserve these axioms after every completed event.

## C.4 Wheeler index

List edges by source-node Wheeler order, with the route's canonical
within-source label and destination tie breaking. Let \(L_t\) be the resulting
edge-label sequence. The index contains:

- \(L_t\).
- Cumulative symbol counts \(C_t[c]\).
- Canonical bitvectors for node boundaries and edge destinations.
- Exact `rank_c(L_t,k)` and `select_c(L_t,j)` support.
- An occurrence map from accepted graph states to prior completed positions.

For a pattern \(P=c_1\cdots c_k\), backward search begins with the full Wheeler
interval and applies the frozen rank-based interval recurrence supplied by
\(R_C\). The resulting interval must equal exactly the set of graph states
reachable by paths labeled \(P\).

## C.5 Required construction

Construct

\[
\mathcal W=(\eta,\mathfrak B,\rho,\mu,\beta),
\]

where:

1. \(\eta\) maps each completed causal event to a represented Wheeler label.
2. \(\mathfrak B\) is the online Wheeler graph and index builder.
3. \(\rho\) performs backward search and returns zero or more occurrence
   positions \(u<t\) from the resulting interval.
4. \(\mu\) assigns finite integer candidate weights.
5. \(\beta\) combines candidate votes with a represented fallback and returns
   a numerator in \(\{1,\ldots,2^r-1\}\).

Two completed histories are suffix-equivalent at depth \(k\) exactly when
their represented length-\(k\) event suffixes produce the same Wheeler search
interval. Any broader equivalence introduced by \(\eta\) must be explicit in
`C_C` and is tested through the same graph axioms.

Every retrieved occurrence and every candidate continuation bit must lie in
the reconstructed prefix. Ordering, ties, graph updates, rank/select layout,
occurrence insertion, eviction, collision handling, and fallback are finite
and canonical.

## C.6 Organizer-owned controls

The four controls are frozen in \(R_C\) before submissions:

```text
C0  fallback numerator with no index lookup
C1  exact-event Wheeler labels with submitted capacities
C2  submitted labels, graph, retrieval, and blend
CR  submitted construction with the frozen nonidentity label permutation
```

The control adapters fix initialization, capacities, coder semantics,
finalization, permutation, and accounting. Contestants provide no control
implementation. Missing control output invalidates the audit, but controls
provide no acceptance credit.

## C.7 Proof obligations

Prove:

- Every graph prefix satisfies all Wheeler axioms.
- Edge ordering and bitvector layout are canonical.
- Rank and select results match direct enumeration.
- Backward-search intervals match path-labeled state sets.
- The stated suffix-equivalence condition holds.
- Every retrieved position satisfies \(u<t\).
- Index contents and occurrence ordering agree in encoder and decoder.
- Every candidate-derived bit is already reconstructed.
- Collision, eviction, exhaustion, and fallback are deterministic.
- Numerators and all dynamic state satisfy their bounds.
- The exact submitted route satisfies \(L_C\le T_C\).

## C.8 Pass condition

Problem C passes exactly when

\[
L_C\le T_C,
\]

\[
|C_C|\le B_{C,C},
\qquad
\operatorname{IndexBits}_C\le B_{C,I},
\]

\[
\operatorname{Ops}_C\le B_{C,O},
\qquad
\operatorname{Mem}_C\le B_{C,M},
\]

and every common Seal gate passes.

A valid Problem C solution is complete and uses no result from Problems A, B,
D, or E.

---

# Problem D: Integer Dynamical Realization

## D.1 Objective

Replace a separately supplied rational teacher with a bounded integer
dynamical system whose complete exact coded length and resources satisfy an
absolute target.

## D.2 Supplied data

Problem D supplies its own finite teacher

\[
\tau_{t+1}=F^*(\tau_t,\omega_t,x_t),
\qquad
p_t^*=G^*(\tau_t,\omega_t),
\]

with:

- An exact initial teacher state.
- Exact rational transition and output semantics.
- A teacher certificate and exact teacher payload.
- A finite integer instruction alphabet \(\mathcal I_D\).
- Exact semantics and operation cost for every instruction.
- Bounds \(B_{D,C},B_{D,S},B_{D,O},B_{D,M}\).
- An absolute target \(T_D\).
- A diagnostic degradation allowance \(\Sigma_D\).

The teacher belongs only to Problem D construction data. It is not available
at candidate runtime unless represented and charged in `C_D`.

## D.3 Required construction

Construct

\[
\mathcal K=(U,u_1,\widehat F,\widehat G),
\]

where:

- \(U\) is a finite bounded-integer state space.
- \(u_1\) is explicit.
- \(\widehat F\) is a finite instruction sequence implementing the transition.
- \(\widehat G\) is a finite instruction sequence producing a dyadic numerator.

The candidate may approximate, factor, quantize, sparsify, reorganize, or
replace the teacher. It may also ignore the teacher and provide a different
bounded construction. The absolute target determines acceptance.

## D.4 Proof obligations

Prove:

- Every instruction has declared integer semantics.
- Every reachable state remains in \(U\).
- Overflow, signedness, division, shifting, lookup, rounding, and saturation
  are defined.
- Teacher construction data is absent from runtime unless charged.
- The integer recurrence is causal and deterministic.
- Encoder and decoder states agree by induction.
- The exact global length difference from the teacher is reported.
- The absolute target and resource inequalities hold.

Per-position rational log loss may be reported only as nonadditive diagnostic
evidence.

## D.5 Pass condition

Problem D passes exactly when

\[
L_D\le T_D,
\]

\[
|C_D|\le B_{D,C},
\qquad
\operatorname{StateBits}(U)\le B_{D,S},
\]

\[
\operatorname{Ops}_D\le B_{D,O},
\qquad
\operatorname{Mem}_D\le B_{D,M},
\]

and every common Seal gate passes. The diagnostic inequality

\[
L_D-L_{\mathrm{teacher}}\le\Sigma_D
\]

may be required by a particular instance, but it never replaces the absolute
target.

A valid Problem D solution is complete and uses no result from Problems A, B,
C, or E.

---

# Problem E: Prototype-Coset Reconstruction

## E.1 Objective

Construct an exact block representation using causal prototypes and explicitly
paid residual identifiers. The representation may use edit descriptions,
finite parity cosets, or a canonical mixture, but every block must reconstruct
exactly under bounded search.

## E.2 Supplied data

Problem E supplies:

- A block partition specific to this route.
- A finite prototype grammar.
- Permitted causal prototype-bank updates.
- A finite family of binary check-matrix constructors.
- A finite residual-energy grammar.
- A fixed bounded deterministic residual decoder.
- Bounds \(B_{E,C},B_{E,Z},B_{E,S},B_{E,O},B_{E,M}\).
- An absolute target \(T_E\).

A runtime prototype may be fixed in `C_E` or generated from completed earlier
blocks. It may not depend on an unreconstructed current or future block.

## E.3 Required construction

Construct

\[
\mathcal P=(\Pi,\mathcal B,\mathcal R,\mathcal H,\mathcal D).
\]

It consists of:

1. A finite prototype-selection rule \(\Pi\).
2. A bounded causal prototype bank \(\mathcal B\).
3. A finite explicit-edit grammar \(\mathcal R\).
4. A finite nested parity family \(\mathcal H\), possibly empty.
5. A deterministic bounded reconstruction rule \(\mathcal D\).

For each block, the paid record in `Z_E` declares one mode:

```text
literal
prototype plus explicit edit
prototype plus syndrome
prototype plus syndrome plus literal residual
```

Every prototype identifier, mode, edit, syndrome bit, search-depth choice,
exception, and literal residue is represented exactly once. Literal mode must
always be available.

For a syndrome mode, the submission must define:

- The exact matrix and its rank over \(\operatorname{GF}(2)\).
- The exact candidate ordering.
- The exact tie-breaking rule.
- The exact expansion and memory budget.
- The unique candidate returned by the bounded decoder.

The encoder may choose a mode after inspecting the complete block because the
complete mode record and residual are paid before reconstruction of that block.

## E.4 Proof obligations

Prove:

- Every selected prototype is available at its release time.
- The prototype bank evolves identically in encoder and decoder recurrences.
- Every explicit edit is uniquely invertible.
- Every accepted syndrome reconstruction returns exactly the intended block.
- Every failed bounded search selects a represented fallback.
- Every matrix, rank, search rule, and energy constant is finite and charged.
- The concatenated reconstructed blocks equal \(x\).
- The exact target and resource inequalities hold.

## E.5 Pass condition

Problem E passes exactly when

\[
L_E\le T_E,
\]

\[
|C_E|\le B_{E,C},
\qquad
|Z_E|\le B_{E,Z},
\]

\[
\operatorname{StateBits}_E\le B_{E,S},
\qquad
\operatorname{Ops}_E\le B_{E,O},
\qquad
\operatorname{Mem}_E\le B_{E,M},
\]

and every common Seal gate passes.

A valid Problem E solution is complete and uses no result from Problems A, B,
C, or D.

---

# II. Strict solution standard

For any attempted route, the contestant must submit:

- Every finite mathematical object required by that route.
- Canonical serializer input for `C` and `Z`.
- Exact integer channel lengths.
- Exact state, operation, and memory ledgers.
- Causality, closure, replay, and target proofs.
- Any route-specific proof required above.

The proof channel `P` is verifier-only. It cannot initialize state, provide a
prediction, resolve a tie, choose a mode, or supply any reconstruction bit.

The following are never sufficient:

- Forecasts.
- Prefix extrapolations.
- Ideal entropy or log-loss without exact coding.
- Oracle labels without their charged codewords.
- Independently added savings.
- Uncounted model information.
- Hidden teacher traces.
- Probabilistic correctness.
- Expected runtime.
- A construction that requires another route.

---

# III. Final independence theorem

Let \(V_i\) be the Seal verifier restricted to route \(i\). The organizer must
establish before release that each \(V_i\) loads only:

- The common frozen instance.
- The common Seal.
- Route \(i\)'s disjoint runtime object \(R_i\), adapter, and bounds.
- Route \(i\)'s submitted `C`, `Z`, `Y`, `F`, and `P` objects.

It loads no submitted artifact or fixed dependency from any other route.

The examination passes exactly when

\[
\exists i\in\{A,B,C,D,E\}:V_i=\operatorname{PASS}.
\]

Thus every problem is a complete alternative theorem, not a stage in a shared
pipeline.
