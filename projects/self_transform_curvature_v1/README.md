# Curvature-aware state factorial: admission protocol

**Not a measured optimizer result.** This freezes the next representational
hypothesis and implements the shared scalar observation boundary. Learned curvature
updates, Adam/L-BFGS comparators and the full run remain unimplemented.

## Why not append momentum to v7?

V7 changed its meta-training population each generation. A BFGS secant formed
between gradients of different objectives is not a valid curvature observation.
Simply carrying that state would give a misleading state-vs-no-state comparison.
This protocol fixes one meta-training objective within each three-generation chain,
uses fresh holdouts for scoring, and rejects history from a different objective.
Downstream task evaluation always starts with empty state, so stale training history
cannot masquerade as fresh-target ability.

## Genuinely different representation

Proposed update: a dimension-independent rank-two preconditioner rather than an
independent rate per coordinate. Build an orthonormal basis U from the current
estimated gradient and the previous secant direction. Learn a small 2x2 positive
matrix using a Cholesky factor L, with normalized gradient, step and curvature
features. Then apply `delta = -eta [I + U (L L^T - I) U^T] g`.

This changes direction using cross-coordinate geometry. Degenerate bases reduce
to identity preconditioning. Bound eigenvalues and step norms in the frozen
implementation, and record clamps as part of the mechanism. Positive definiteness
relative to estimated gradients does not guarantee true-loss descent.

The same 16-parameter feature rule must operate on task parameters and its own
16 coefficients. Export all coefficients, current optimizer history, objective
identity, dimensions and rule version. Exact restoration is a correctness property,
not the source of intelligence. The fixed interpreter remains explicit.

## Attribution and cost

Factor current versus fixed initial proposer with retained versus reset meta-history.
Add training-calibrated Adam and two-pair L-BFGS, both using the same eight scalar
loss observations per update. No analytic derivative, Hessian, task optimum,
line search or uncharged acceptance query is allowed. All methods receive the same
public task descriptor and scalar observations; actual memory/arithmetic may differ
and must be reported within a shared state-capacity allowance.

Both direct downstream optimization and meta-rule improvement need distinct reports.
A meta-rule result does not automatically beat Adam on training neural networks.
Retaining optimizer state may help a fixed proposer; only the current-vs-fixed
contrast under the same history policy attributes value to inherited rule changes.
The protocol requires separate-family results and retains conventional comparators.

## Prior art and scope

[Metz et al. (2020)](https://arxiv.org/abs/2009.11243) already study learned optimizers
that can train themselves. [Celo2](https://arxiv.org/abs/2602.19142) motivates normalized
optimizer features and meta-training diversity. An [independent VeLO evaluation](https://proceedings.mlr.press/v239/rezk23a.html)
shows why genuinely tuned conventional baselines matter. These sources motivate
the investigation; they do not establish this proposed mechanism's novelty or success.

## Admission check

`node projects/self_transform_curvature_v1/test.mjs`

Checks enforce eight calls, charge failed oracle calls, copy history to prevent
aliasing and reject mismatched objective/dimension reuse. This is a correctness
check for the protocol boundary, not qualification of an optimizer. No GPU or
external model download is needed. Generated receipts will remain local.
