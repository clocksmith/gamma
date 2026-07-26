# Private Rubric for the Atlas and Clockwork Mathematical Examination

Classification: `ORGANIZER ONLY`
Rubric version: `ACS-MATH-RUBRIC-1`
Required Seal: `ACS-MATH-SEAL-1`

## 1. Solver-facing boundary

This rubric must not be sent to solvers as part of the examination. The solver
receives only:

```text
atlas_clockwork_seal_problem_set.md
```

The solver submits one mathematical manuscript. No software, numerical corpus,
archive, table bundle, manifest, schema, benchmark, or execution receipt is
required.

## 2. Mathematical verdicts

Each problem receives one verdict:

```text
COMPLETE
INCOMPLETE
INCORRECT
NOT_ATTEMPTED
```

- `COMPLETE` means every requested theorem, construction, proof, sharpness
  claim, and counterexample obligation is correct.
- `INCOMPLETE` means the principal argument may be correct but at least one
  requested result or case is missing.
- `INCORRECT` means a claimed theorem, construction, or proof contains a
  substantive error.
- `NOT_ATTEMPTED` means no solution was submitted for that problem.

A complete solution to any one independent problem passes the public
examination.

## 3. General mathematical standards

A complete solution must:

- State every newly introduced object precisely.
- Prove existence before using a selected object.
- Separate necessary from sufficient conditions.
- Treat finite boundary and zero-count cases.
- Give explicit constructions where requested.
- Prove claimed optimality or sharpness.
- Identify every dependence of a bound.
- Avoid reliance on numerical experiments.
- Avoid assuming another examination problem.

Published theorems may be cited in standard form. A specialized result central
to the requested conclusion must be proved or reduced transparently to a
published theorem.

## 4. Problem A grading

Problem A is `COMPLETE` only if the manuscript establishes:

1. The exact relaxed variational formula.
2. Existence and characterization of optimizing weights.
3. Correct treatment of unused explanations.
4. Constructive conversion from relaxed weights to a binary prefix code.
5. The best proved universal integer-prefix gap, with matching examples when
   sharpness is claimed.
6. A necessary-and-sufficient description-priced threshold condition.
7. The sharp perturbation bound and equality cases.

A rowwise numerical optimizer, unproved alternating procedure, or fixed-gain
example is incomplete.

## 5. Problem B grading

Problem B is `COMPLETE` only if the manuscript establishes:

1. The direct behavioral equivalence
   \[
   h\equiv h'
   \Longleftrightarrow
   \forall u\in A^*,
   \operatorname{Trace}(h,u)=\operatorname{Trace}(h',u).
   \]
2. Color preservation and right-congruence properties.
3. Unique coarseness.
4. Finite distinguishing words and a proved length bound.
5. Finite minimality certificates.
6. The Wheeler interval theorem.
7. A converse with every required hypothesis or counterexample.
8. A correct resolution of canonical minimal Wheeler refinement.
9. A continuation-interval bound and extremal examples.

A deterministic transducer without an explicit quotient theorem is
incomplete. An index implementation is irrelevant to the mathematical verdict.

## 6. Problem C grading

Problem C is `COMPLETE` only if the manuscript establishes:

1. A uniform state bound valid for every input sequence and length.
2. Exact dependence on contraction and all approximation errors.
3. The sharp base-two logistic-loss Lipschitz constant.
4. A cumulative excess-loss theorem valid for every outcome sequence.
5. A rational Householder-plus-sparse approximation theorem.
6. A characterization of exact zero-residual realizability.
7. An explicit precision threshold for prescribed cumulative allowance.
8. Sharpness examples or lower bounds for principal terms.

Simulation, average-case stability, or an argument depending on one selected
input sequence is incomplete.

## 7. Problem D grading

Problem D is `COMPLETE` only if the manuscript establishes:

1. The exact kernel-based collision characterization.
2. Sharp relations among successful parity depth, rank, and collisions.
3. A proof or disproof of a universal nested family with constant overhead.
4. The strongest valid replacement theorem if universal constant overhead is
   impossible.
5. Unique-coset theorems for structured residual balls.
6. Matching constructions and obstructions for the required examples.
7. A finite bounded-search uniqueness certificate.
8. A lower bound on certificate information when claimed.

Empirical syndrome tests or probabilistic collision estimates do not complete
the problem.

## 8. Independence audit

A problem solution may not cite another requested result from this examination.
If a proof relies on a lemma identical to another problem's requested theorem,
the solver must prove that lemma independently within the attempted solution or
cite a preexisting published theorem.

One problem's incompleteness or incorrectness cannot affect an independently
complete solution to another problem.

## 9. Public examination decision

The public examination passes exactly when at least one problem is graded
`COMPLETE`.

The organizer reports mathematical verdicts separately. It does not mention
private applications, hidden datasets, compression targets, implementation, or
transfer in solver-facing feedback.

## 10. Private application review

After a public solution is graded `COMPLETE`, a separate organizer team applies
the private Seal.

The application team must not alter the solver's theorem. It may instantiate
variables, derive finite parameters, and implement the construction exactly as
the theorem permits.

Private transfer receives one status:

```text
TRANSFER_PASS
TRANSFER_FAIL_HYPOTHESES
TRANSFER_FAIL_CONSTRUCTION
TRANSFER_FAIL_TARGET
TRANSFER_FAIL_RESOURCES
TRANSFER_INVALID
```

A mathematically complete proof does not automatically receive
`TRANSFER_PASS`. Transfer requires the corresponding private hypothesis,
construction, and exact verifier receipts.

## 11. Separation of claims

Public claim:

> The solver completed an independent mathematical problem.

Private transfer claim:

> The organizer proved the hidden application satisfies the theorem's
> hypotheses, instantiated the construction, and verified the resulting exact
> artifact.

These claims must never be conflated. The organizer may reveal the private
claim only when every Seal requirement is satisfied.
