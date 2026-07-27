# FR-1: Exact Selection of One Paid Residual Rule

## Problem

Let observations have categorical decoder-visible coordinates
\(f_1,\ldots,f_d\). Let \(\mathcal R\) be the finite family containing every
rule \(f_i=a\) and every conjunction \(f_i=a,\ f_j=b\) for \(i<j\). Let
\(\mathcal E\) be a finite family of deterministic probability corrections,
including the identity.

For a rule \(R\) and expert \(e\), define its training gain over identity as
the exact integer log-loss reduction on observations satisfying \(R\), minus a
fixed description price \(D(R,e)\). Outside \(R\), the identity is used.

Prove:

1. Exhaustive aggregation by rule category and expert returns the exact
   maximum-gain one-rule model.
2. Choosing the identity on a nonpositive maximum and lexicographic
   \((R,e)\) order on ties is canonical and inclusion-minimal.
3. If all coordinates and expert probabilities are known before truth, the
   frozen rule is a causal predictor.
4. Exact training optimality gives no holdout guarantee; sealed chronological
   replay is required.

Give time and storage bounds in terms of observations, rule families,
categories, and experts.
