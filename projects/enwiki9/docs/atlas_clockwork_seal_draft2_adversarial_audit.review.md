# Review: ACS-MATH-DRAFT-2-WORKING Adversarial Audit

Review date: `2026-07-26`
Review class: expert mathematical specification review
Submission class: not an examination solution

## Verdict

`PASS WITH FORMAL ERRATA`

No new counterexample was found to the substantive theorems in Problems A-D
after applying the recorded C1, D3, and D4 corrigendum. The accepted solutions
remain mathematically complete under those interpretations.

Draft 2 was not ready to freeze before this review. The audit identified:

1. A missing finite-precision feasibility condition in C4.
2. Undefined Hamming-ball radii in D3.
3. Missing \(B\) and \(j\) domains in D4.
4. Informal continuation-set and unfolding-canonicality language in B2-B3.
5. A constructivity gap for arbitrary real-valued energies in D2.
6. Undefined and unused sparsity language in C3.
7. An overclaim in Route C's transfer map about selecting a factorization.

All seven findings are incorporated into `ACS-MATH-DRAFT-2-WORKING`.

## Transfer assessment

No new theorem is warranted at present. Every route is first blocked by an
absent finite application object:

- Route A lacks a positive paid explanation family.
- Route B lacks a positive decoder-visible predictive coloring.
- Route C lacks an exact under-target teacher and frozen useful factorization.
- Route D lacks low-rank, cheaply searchable residual structure.

Those are empirical or engineering obligations. They cannot be discharged by
restating them as pencil-and-paper questions.

## Seal decision

```text
Seal-2:             UNBOUND
authorized routes:  none
compression credit: 0 bytes
```

The organizer must establish an exact full-corpus baseline and one
target-bearing antecedent before any route can be bound. Forecasts, oracles,
proxy losses, and separately added component gains do not qualify.
