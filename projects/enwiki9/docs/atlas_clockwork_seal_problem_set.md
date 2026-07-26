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

## 2. Runtime instance

The organizer separately supplies a frozen runtime object \(R\). It contains
only:

- Fixed finite constants.
- Canonical grammar definitions.
- Exact coder definitions.
- Causal observable generators.
- Route-specific fixed interpreters.
- Route-specific targets and resource bounds.

The runtime object does not contain \(x\), a future-symbol table, an uncharged
prediction trace, or any equivalent encoding of the construction object.

Before reconstructing position \(t\), the interpreter may calculate

\[
\omega_t=\Omega(R,x_{<t},\zeta_{\le t}),
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

The five problems share only \(x\), \(R\), the block boundaries, the Seal, and
organizer-declared causal observables. Each route has a separate namespace,
serializer, fixed-cost ledger, target, interpreter entry point, and verdict.

A verifier evaluating one route must not load any submitted artifact from
another route.

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

# Problem B: Predictive Quotient

## B.1 Objective

Construct a finite quotient of causal histories that shares predictive state
across histories while preserving a deterministic next-state recurrence and
meeting the absolute target without paid block labels.

## B.2 Supplied data

Problem B supplies:

- A finite descriptor alphabet \(\mathcal D_B\).
- A causal descriptor generator
  \[
  d_t=\Delta_B(R,x_{<t}).
  \]
- A finite dyadic probability denominator \(2^r\).
- Bounds \(B_{B,C},B_{B,Q},B_{B,O},B_{B,M}\).
- An absolute target \(T_B\).

No label or selector channel is supplied. Thus \(Z_B\) is empty.

## B.3 Required construction

Construct the finite tuple

\[
\mathcal Q=(Q,q_1,\delta,\nu,E).
\]

It consists of:

1. A finite quotient-state set \(Q\).
2. An initial quotient state \(q_1\in Q\).
3. A deterministic transition
   \[
   \delta:Q\times\mathcal D_B\times\{0,1\}\to Q.
   \]
4. A deterministic numerator map
   \[
   \nu:Q\times\mathcal D_B\to\{1,\ldots,2^r-1\}.
   \]
5. A finite exceptional-transition set \(E\), serialized completely in `C`.

The quotient must be a right congruence on every reachable submitted history:
if two histories occupy the same quotient state and have the same current
descriptor, then equal reconstructed next bits must produce the same next
quotient state, except through an explicitly represented exception in \(E\).

At position \(t\), use

\[
a_t=\nu(q_t,d_t),
\]

then update

\[
q_{t+1}=\delta(q_t,d_t,x_t).
\]

## B.4 Mathematical proof obligations

Prove:

- Every descriptor is causally available.
- The represented relation is finite.
- The transition is single-valued.
- The quotient congruence holds on all reachable states.
- Every exception is represented exactly once.
- Equal runtime histories produce equal states and numerators.
- The exact coded and resource inequalities hold.

An empirical clustering score, approximate state similarity, teacher hidden
state, or nonconstructive minimality theorem is not a solution.

## B.5 Pass condition

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

# Problem C: Exact Continuation Geometry

## C.1 Objective

Construct a bounded causal geometry over previously reconstructed history that
retrieves exact earlier continuations and converts them into an exact
probability measure under the absolute target.

## C.2 Supplied data

Problem C supplies:

- A finite event alphabet \(\mathcal E_C\).
- A causal event generator from reconstructed prefixes.
- Permitted finite index primitives.
- A finite dyadic probability denominator \(2^r\).
- Bounds \(B_{C,C},B_{C,I},B_{C,O},B_{C,M}\).
- An absolute target \(T_C\).

No future index, target-position table, or offline continuation trace is
available at runtime. The index must be rebuilt from reconstructed history.

## C.3 Required construction

Construct the finite tuple

\[
\mathcal W=(\eta,\iota,\rho,\mu,\beta).
\]

It consists of:

1. A finite equivalence-signature map \(\eta\) over completed causal events.
2. A deterministic online index update \(\iota\).
3. A deterministic retrieval map \(\rho\) that returns zero or more candidate
   positions \(u<t\).
4. A finite candidate weighting map \(\mu\).
5. A finite fallback and blending map \(\beta\) producing a numerator in
   \(\{1,\ldots,2^r-1\}\).

At every position, each retrieved candidate bit must already belong to the
reconstructed prefix. A candidate may propose a continuation beginning at an
earlier position, but the map may inspect only the portion already stored in
the runtime index.

The complete ordering, tie breaking, eviction, collision handling, fallback,
and table-capacity rules must be finite and represented in `C`.

## C.4 Required controls

The proof must report exact complete lengths for:

```text
C0  fallback measure without retrieval
C1  exact-history retrieval only
C2  submitted equivalence retrieval
CR  submitted index with deterministic signature permutation
```

Controls provide diagnostics only. Passing depends exclusively on the absolute
submitted-route target.

## C.5 Proof obligations

Prove:

- Every retrieved position satisfies \(u<t\).
- Index contents are identical in encoder and decoder recurrences.
- Equal indexed histories produce equal candidate orderings.
- Collision and eviction rules are deterministic.
- Every candidate-derived bit is already known at prediction time.
- The numerator is always within the dyadic range.
- All dynamic state satisfies the index and resource bounds.
- The exact submitted route satisfies \(L_C\le T_C\).

## C.6 Pass condition

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
- Route \(i\)'s fixed adapter and bounds.
- Route \(i\)'s submitted `C`, `Z`, `Y`, `F`, and `P` objects.

It loads no artifact from any other route.

The examination passes exactly when

\[
\exists i\in\{A,B,C,D,E\}:V_i=\operatorname{PASS}.
\]

Thus every problem is a complete alternative theorem, not a stage in a shared
pipeline.
