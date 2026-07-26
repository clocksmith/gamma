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

## Planned ACS-MATH-DRAFT-2

The next draft must:

1. Apply the corrected D3 hypothesis or subset formulation.
2. Bind D4's count to the canonical sequential direct verifier.
3. Preserve the remaining Problem D statements unless separately amended.
4. Receive a new SHA-256 and changelog entry.
5. Undergo a fresh private Seal binding audit.

No existing submission will be retroactively graded against
`ACS-MATH-DRAFT-2`.

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
