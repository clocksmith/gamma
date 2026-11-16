# Curvature-aware state factorial

Implemented CPU-only follow-up after v7's failed hereditary attribution result.
This tests cross-coordinate curvature and retained optimizer state instead of
continuing to sweep the four-coefficient rate mechanism. Previous studies remain
unchanged. Protocol execution details and source hashes were fixed before the run.

## Mechanism

Sixteen coefficients map four normalized features (bias, gradient magnitude,
gradient alignment and secant curvature) into a 2x2 Cholesky factor and step-size.
Build orthonormal U from the estimated gradient and prior displacement, then:

```
M = 0.1 I + 1.9 (L L^T) / lambda_max(L L^T)
delta = -eta [I + U (M - I) U^T] g
eta = exp(-4 + clamp(z_step, -2, 2))
```

M has eigenvalues in [0.1, 2]. Degenerate second basis directions contribute zero.
Every method, including comparators, shares the step-norm cap `0.25*(1+norm(theta))`.
This ensures bounded updates, not true-loss descent under noisy gradient estimates.
The same learned rule accepts task parameters and its own16 coefficients.

The external oracle returns eight scalar losses at four symmetric perturbations.
Gradient estimates are decoded from those observations, never analytic derivatives.
All methods share probe geometry and radius. Adam uses declared moments and bias
correction. L-BFGS uses two secant pairs, skips nonpositive curvature and performs
no line search. No method receives optimum/Hessian information or a free retry.

## State and comparison design

The meta-training support objective is **fixed within a three-generation chain**.
This repairs v7's incompatibility with meaningful secant retention: gradients from
different objectives cannot be treated as curvature of one objective. Histories
are tagged by objective and dimension, copied and rejected if reused incorrectly.

Factor current/fixed initial proposer with retained/reset meta-history. Add tuned
Adam and L-BFGS updates of the same learned-rule parameters. Downstream scoring
always starts a fresh task with empty optimizer state. These are meta-rule update
comparisons, **not direct evidence of beating Adam/BFGS on downstream optimization**.

Rule coefficients and full history roundtrip through exact little-endian float64
artifacts before each next generation. Tests show resumed output parity. This run
uses pure functions in one process, not independent process isolation; prior v7
separately tested that property. Reconstruction is portability/integrity, not a
source-printing quine or evidence of autonomous RSI.

## Frozen scope and budgets

Twelve independently seeded replicates per family:2D rotated positive-definite
quadratics (condition ratios1-100) and8D regularized logistic regression. These two
families have different dimensions, so do not attribute family differences solely
to loss shape. Each held-out generation has64 new tasks,12 adaptation steps.

Initial rule selection searches33 random candidates on two training tasks with
four steps. Each conventional comparator then searches33 settings using three
meta-update generations and separate two-task support/query populations. Adam
calibrates eleven rates crossed with three moment factors; L-BFGS calibrates33
rates. Both ranges span0.0001 to1.0. Training and calibration populations are
separate from the four-task evaluation meta-support and64-task held-out sets.

Per replicate, actual shared initialization costs2,178 scalar calls; each of the
two comparator calibrations costs59,598. Every hypothetical arm is charged all
121,374 calls, including calibration it does not use. This equalizes charged
available preprocessing, **not useful training work**: rule initialization and
comparator calibration use different objectives. Per evaluation update every arm
uses exactly3,112 scalar calls (eight outer meta calls plus3,104 inner task calls)
and385 update operations. Report nesting explicitly; outer and task-level scalar
calls are not interchangeable. Each parent/child scoring pair costs12,416 scalar
calls and1,536 updates. Arithmetic, clamps, skipped curvature and state bytes are
recorded. State capacity is8*d+32 numeric scalars; JSON byte overhead is separate.

## Results: neither family clears hereditary threshold

Primary current-vs-fixed retained-state contrast at generation3 requires median
relative loss reduction at least1% and exact one-sided sign p below0.025 **per
family**. Fresh-target results:

| Family | Wins/losses | Median relative benefit | Sign p | Decision |
| --- | --- | ---: | ---: | --- |
| Quadratic | 8/4 | 0.014710% | 0.193848 | Fail |
| Logistic | 12/0 | 0.004900% | 0.000244 | Fail practical magnitude |

The logistic direction is consistent but the effect is tiny. A significant sign
test alone does not satisfy the frozen practical criterion. Descriptive median
order-statistic intervals are -3.152686% to12.662828% for quadratic, and0.000659%
to0.019984% for logistic (approximately96.14% coverage with independent exchangeable
replicate effects). The samples do not establish broad generalization.

State retention is more consequential than changing the learned rule: current
retain versus current reset median benefit is6.475457% on quadratic and0.217521%
on logistic. This is ordinary optimizer-history behavior, not proof of heredity.

Comparator outcomes are mixed: on quadratic, current retained rule beats tuned
Adam10/12 with median26.545213% loss reduction, but L-BFGS only6/12. On logistic,
it loses11/12 to Adam (median11.569146% higher loss) and12/12 to L-BFGS (median
6.735840% higher loss). These secondary comparisons do not rescue the failed
primary hereditary test. Within-parent improvements occurred17/36 quadratic and
36/36 logistic transitions; shared ancestry means those are not independent seeds.

All432 arm/generation records completed. First CPU run took17.63 seconds including
training, calibration and scoring. Every artifact roundtrip and query/state budget
check passed. Raw receipts remain local, including negative outcomes. No GPU,
model downloads, production services or private receipt publication.

## Conclusion and next decision

This representational change produced task-specific curvature/memory behavior,
not a useful measured hereditary rule-changing advantage. Do not claim RSI from
its12/12 tiny logistic gains. A stronger future mechanism would need a task where
learned rule changes contribute beyond a fixed learned rule with identical state,
and tuned conventional controls; changing tests to manufacture that outcome is
not evidence. Preserve this null primary result rather than continuing seed sweeps.

## Prior art

[Metz et al.2020](https://arxiv.org/abs/2009.11243) already investigate learned
optimizers that train themselves. [Celo2](https://arxiv.org/abs/2602.19142) motivates
normalization and training diversity; [independent VeLO evaluation](https://proceedings.mlr.press/v239/rezk23a.html)
underscores tuned-baseline comparisons. No novelty claim is made here.

## Commands

```
node projects/self_transform/self_transform_curvature_v1/test.mjs
node projects/self_transform/self_transform_curvature_v1/run.mjs .work/curvature-state-new.json
node projects/self_transform/self_transform_curvature_v1/analyze.mjs .work/curvature-state-new.json
```
