# Adversarial Audit of ACS-MATH-DRAFT-3-WORKING

## Verdict

`MATHEMATICALLY COMPLETE; NOT TRANSFER-BOUND`

No false fixed theorem was found in Problems A-D. The statements incorporate
the prior corrections for optimizer closure, total-system interval counts,
admissible versus supremal sharpness, finite-precision feasibility, empty
residual families, exact energy comparison, and canonical sequential
verification.

## Independent sharpness checks

### Problem A

Use two explanations and force \(J-1\) rows to explanation one and one row to
explanation two by a sufficiently large finite gain separation. The relaxed
optimal weights are

\[
\left(1-\frac1J,\frac1J\right).
\]

Any active binary two-word prefix code has both lengths at least one, whereas
the relaxed average price is the binary entropy of \(1/J\). Hence the
normalized integer gap is

\[
1-H_2(1/J)\longrightarrow1.
\]

This supplies the requested asymptotic sharpness family.

### Problem B

For a total deterministic quotient with at least two states, the initial color
partition has at least two blocks; otherwise the universal relation is a
color-preserving right congruence. Every nonterminal refinement is strict, so
pairwise distinguishing length is at most \(|Q|-2\). Totality also makes every
continuation image nonempty, removing the partial-system empty interval.

### Problem C

The contractive recurrence proof is the exact scalar affine-error recurrence
followed by a finite geometric sum. The statement correctly restricts exact
attainment to compatible rational/lattice instances and asks only for
supremal sharpness at arbitrary real \(\rho\). The finite-precision clause
correctly separates any \(m\)-independent error floor.

### Problem D

For sharpness, choose a \(d\)-dimensional subspace \(U\), a point \(x\), and an
exact energy order placing precisely \(x+U\setminus\{x\}\) before \(x\).
Then

\[
S_x=U\setminus\{0\},\qquad r_E(x)=2^d.
\]

Every successful linear map is injective on \(U\), so its rank and row count
are at least \(d\). A \(d\)-row map injective on \(U\) attains the bound.

## Remaining boundary

Draft 3 is a solved theorem bank, not a hidden reduction to a score-bearing
compressor. Its conclusions require empirical predictors, finite application
objects, implementations, and exact resource receipts before they can affect
enwiki9. It must remain expert-review material unless a separate precommitted
binding artifact supplies those antecedents.
