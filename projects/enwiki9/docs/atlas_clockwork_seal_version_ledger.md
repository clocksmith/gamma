# Atlas-Clockwork Seal Version and Errata Ledger

This ledger records immutable problem hashes, solution-triggered errata, and
version evolution. It does not authorize candidate distribution or Seal
binding.

## ACS-MATH-DRAFT-1

```text
artifact:
  docs/atlas_clockwork_seal_problem_set.md
sha256:
  3813484e6a0e035c9c8141d332d039ffaa36831e3f1efda460e9e52027a8926f
source_bound_gamma_commit:
  a13f7250
state:
  FROZEN_FOR_RECORDED_SUBMISSIONS
seal_state:
  UNBOUND
```

This hash, rather than the mutable filename alone, identifies the problem
version governing the registered Problem D submission.

### Erratum D3

The phrase "arbitrary finite \(B\)" permits \(B=\varnothing\). For that case,

\[
B-B=\varnothing
\]

and the equality

\[
\ker H\cap(B-B)=\{0\}
\]

is false even though every kernel coset meets \(B\) at most once.

The universally valid statement is:

\[
\ker H\cap(B-B)\subseteq\{0\}.
\]

Alternatively, retain equality and add the hypothesis \(B\ne\varnothing\).
This is a semantic correction and requires a new problem version.

### Erratum D4

Exactly \(j\) matrix-vector evaluations are required by the specified
candidate-by-candidate direct scan. This is not a universal lower bound for
arbitrary verifiers, which may exploit linear dependence or a specialized
representation of \(H\).

The next problem version must explicitly bind the claim to the canonical direct
verifier or define a computational model strong enough to support a lower
bound. This is a semantic clarification and requires a new problem version.

## ACS-MATH-DRAFT-2

```text
artifact:
  docs/atlas_clockwork_seal_problem_set.md
sha256:
  c1a6f63d94f8568ecd7b56968ad849977edfcd2c94a9c5ba11f24073f0055fa2
source_bound_gamma_commit:
  3824395f
state:
  FROZEN_MATHEMATICAL_ARTIFACT
seal_state:
  UNBOUND
```

This frozen mathematical draft:

1. Replaces C1's unconditional exact-attainment demand with exact attainment
   for admissible rational contraction factors and supremal sharpness for every
   real contraction bound.
2. Replaces D3's equality by the universally valid subset condition and
   recovers equality under the explicit hypothesis \(B\ne\varnothing\).
3. Binds D4's \(j\)-evaluation count to the canonical sequential verifier and
   disclaims an unrestricted verifier lower bound.
4. Preserves the remaining statements from `ACS-MATH-DRAFT-1`.

### Draft 2 adversarial audit

An expert audit after the initial C1, D3, and D4 corrections found no new
counterexample to the substantive A-D theorems. It identified seven formal
issues that are incorporated into the working draft:

1. C4 now distinguishes nearest-rounded initial state from an externally fixed
   error floor and requires explicit finite-precision feasibility.
2. D3 now defines Hamming balls and restricts all radii to integers.
3. D4 now defines the domains of \(B\) and \(j\), including empty search.
4. B2 and B3 now define continuation endpoint sets, require integer depth, and
   make the unfolding relative to a supplied state order.
5. D's energy has a finite exact representation and decidable comparator.
6. C3 removes qualitative, unused sparsity terminology.
7. The Route C transfer map now treats the factorization as a frozen supplied
   antecedent rather than a theorem-generated optimum.

These corrections do not alter the Seal decision or provide compression-score
credit.

The exact SHA-256 and source lineage are recorded above. The mathematical audit
is complete, but this artifact cannot govern a candidate examination unless an
independent future Seal decision reports `BOUND`. No existing submission is
retroactively graded against this draft.

## Submission ACS-ABC-20260726T203531Z-b7dd49a0

`ACS-MATH-DRAFT-1` received a normalized combined solution for Problems A,
B, and C at `2026-07-26T20:35:31Z`.

`A` and `B` are mathematically complete as written. `C` is complete
with the following semantic qualification.

### Erratum C1

Under the requirement that scalar recurrence coefficients are rational, an
arbitrary irrational bound \(\rho\) cannot generally be attained exactly in
dimension one. Replace unconditional exact attainability with:

\[
\text{exact attainment for attainable }\rho,
\qquad
\text{supremal sharpness for every real }\rho\in[0,1).
\]

This changes the literal sharpness requirement and must be incorporated into
`ACS-MATH-DRAFT-2`. Existing submissions remain governed by the original
problem hash.

The submission and review are recorded at:

`docs/atlas_clockwork_seal_problems_abc_solution.md`

`docs/atlas_clockwork_seal_problems_abc_solution.review.md`

## Solver-confirmed corrigendum C1/D3/D4

Received at `2026-07-26T21:21:37Z` and recorded as
`ACS-CORRIGENDUM-20260726T212137Z-282aaa6a`.

The solver formally confirmed the C1 admissible-attainment interpretation, the
D3 nonempty-set/inclusion correction, and the D4 canonical-sequential-verifier
scope. The confirmation applies to submissions
`ACS-ABC-20260726T203531Z-b7dd49a0` and
`ACS-D-20260726T202536Z-273dbe2f`.

This closes the mathematical errata review for `ACS-MATH-DRAFT-1`. It does
not create a target-bearing antecedent, authorize distribution, change Seal-2
from `UNBOUND`, or receive compression-score credit.
