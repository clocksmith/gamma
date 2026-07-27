# FR-1 Solution: Exact Selection of One Paid Residual Rule

For each rule category and expert, sum the supplied integer loss over exactly
the observations matching that category. The identity loss over the same set
is accumulated simultaneously. Their difference minus the description price
is precisely the objective value of that one-rule model, because all
nonmatching observations use identity and cancel.

The candidate family is finite, so scanning every pair returns its exact
maximum. If the maximum is nonpositive, the empty identity model has value
zero and is inclusion-minimal. Otherwise, fixed family, category, and expert
orders select the first maximizer canonically.

At prediction time, decoder-visible categorical coordinates select whether
the frozen rule fires. The selected expert is deterministic and evaluated
before truth. Encoder and decoder therefore compute the same probability by
induction; updates to any causal coordinates occur only afterward.

This proves only finite training optimization. Selection can exploit accidental
training correlations, so neither positive training gain nor description
pricing proves transfer. Exact chronological holdout and full arithmetic
replay remain mandatory.

If family \(r\) has \(C_r\) categories, aggregation costs
\(O(n|\mathcal R_{\rm families}||\mathcal E|)\) additions and stores
\(O(|\mathcal E|\sum_r C_r)\) loss totals.
