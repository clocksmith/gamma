# Private Rubric for the Atlas and Clockwork Mathematical Examination

Classification: `ORGANIZER ONLY`
Rubric version: `ACS-MATH-RUBRIC-2`
Required Seal: `ACS-MATH-SEAL-2`
Required Seal status for distribution: `BOUND`

## 1. Solver-facing boundary

This rubric is not sent to solvers. The solver receives only:

```text
atlas_clockwork_seal_problem_set.md
```

The submission is one pencil-and-paper mathematical manuscript. No program,
dataset, archive, benchmark, manifest, or execution receipt is requested.

## 2. Mathematical verdicts

Each independent problem receives exactly one verdict:

```text
COMPLETE
INCOMPLETE
INCORRECT
NOT_ATTEMPTED
```

`COMPLETE` means every fixed theorem, construction, edge case, and sharpness
obligation stated in that problem is proved. There are no discretionary
"strongest possible" or "weakest hypotheses" grading clauses.

The public examination passes if and only if at least one independent problem
is `COMPLETE`.

A `COMPLETE` verdict establishes the corresponding proposition \(T_i\). The
private application team does not parse the manuscript for an executable
witness; it applies the proof-independent canonical map frozen by Seal-2.

## 3. General standards

A `COMPLETE` solution must:

- Define every introduced object.
- Prove existence before selection.
- Separate necessity and sufficiency.
- Treat zero, empty, and finite boundary cases.
- Give each requested explicit construction.
- Prove each stated constant and sharpness example.
- Depend on no other examination problem.
- Use no numerical experiment as proof.

## 4. Problem A grading

Problem A is `COMPLETE` only if it proves:

1. The exact assignment-entropy dual formula.
2. Existence and the complete optimizer characterization, including zero
   weights.
3. The fixed inequality
   \(\mathcal V^*(G)-J\le V^*(G)\le\mathcal V^*(G)\).
4. A legal constructive prefix code with inactive zero-weight explanations.
5. Existence of \(L(n)\) and the exact description-priced threshold theorem.
6. The perturbation bound \(J\varepsilon\), its optimality, and equality cases.

## 5. Problem B grading

Problem B is `COMPLETE` only if it proves:

1. Behavioral equivalence is the unique coarsest color-preserving right
   congruence.
2. The \(|Q|-2\) distinguishing-word bound and an attaining family.
3. The requested finite pairwise distinguishing certificate.
4. The exact equivalence between Wheeler order and the stated one-letter
   interval and monotonicity conditions.
5. The interval theorem for every continuation.
6. The depth-\(L\) unfolding is Wheeler and has the stated exact vertex and edge
   counts.
7. The unfolding's interval and finite-certificate claims.
8. The quadratic continuation-interval bound and linear lower-bound family.

## 6. Problem C grading

Problem C is `COMPLETE` only if it proves:

1. The nearest-dyadic Euclidean rounding bound.
2. The stated uniform shadowing inequality and one-dimensional attainment.
3. The sharp base-two logistic Lipschitz constant.
4. The cumulative loss inequality and closed geometric-sum form.
5. The stated Householder-factor perturbation inequality.
6. Rational orthogonal matrices use at most \(d\) rational Householder
   reflections.
7. The widened-intermediate and final-requantization operator bound.
8. The stated precision condition and explicit dimension-dependent dyadic lower
   bound on \(m\).

## 7. Problem D grading

Problem D is `COMPLETE` only if it proves:

1. The exact kernel collision characterization and successful-depth formula.
2. The finite separating-map theorem by both probabilistic and deterministic
   arguments.
3. Dependent-row deletion and extension to a nested full-rank family.
4. The exact difference-set criterion.
5. Its Hamming-ball, minimum-distance, counting, and affine-union consequences.
6. The bounded-search first-hit certificate equivalence.
7. The exact worst-case count of \(j\) matrix-vector evaluations.

## 8. Independence audit

A solution may not cite another requested result from this examination. If it
needs an equivalent lemma, it must prove it independently or cite a preexisting
published theorem. One problem's verdict cannot affect another's.

## 9. Public decision

The organizer reports only the mathematical verdicts. Solver-facing feedback
must not mention private applications, hidden data, implementation, targets, or
transfer.

## 10. Private application review

Distribution is forbidden unless `ACS-MATH-SEAL-2` is `BOUND` by its immutable
artifact manifest. After a `COMPLETE` verdict, a separate organizer team
applies that exact Seal without changing the theorem or frozen canonical map.
Private transfer receives one status:

```text
TRANSFER_PASS
SEAL_INVALID
ORGANIZER_IMPLEMENTATION_FAILURE
```

Every `COMPLETE` solution to a published route must receive `TRANSFER_PASS`.
`SEAL_INVALID` means the organizer published a route without a valid universal
transfer proof. `ORGANIZER_IMPLEMENTATION_FAILURE` means the frozen implication
remains valid but its prescribed instantiation was executed incorrectly.
Neither failure may be attributed to the solver.

## 11. Separation of claims

Public claim:

> The solver completed an independent mathematical problem.

Private transfer claim:

> Before publication, the organizer proved every complete solution to the route
> transfers; after submission, it instantiated the frozen canonical map and
> verified the exact artifact.

The private claim may be revealed only with every Seal receipt.
