# Hereditary scalar-probe experiment v2

This separate CPU toy tests whether the reconstructed child is a better updater,
not merely whether it can serialize itself. It does not alter v1 or Doppler.

## Same interface, external scalar oracle

`T_phi(theta, experience)` accepts task weights or its own four parameters.
Experience contains four fixed Rademacher directions and scalar losses at their
positive/negative perturbations, with radius 0.001. The operator internally forms
`g_i = mean_j[(Lplus_j - Lminus_j) direction_ji / (2 radius)]`, then applies v1's
learned tanh coordinate updater. External code supplies **scalar losses**, not a
precomputed gradient. This is still a derivative-free gradient estimator plus an
externally supplied objective, not oracle-free intelligence. Probe geometry is
fixed rather than self-invented. No claim of novelty is made.

Initial parameters are trained by 32-candidate random search on fresh training
quadratics. Three unconditional child generations follow. Each generation uses
32 fresh meta-training tasks and 128 fresh held-out targets, six adaptation steps.
Every child then becomes the next parent. No outcome selects/rejects a child.

Each proposal executes in a fresh subprocess with only serialized parent/initial
artifacts, fixed protocol and meta-training seed. All proposals are frozen before
holdout scoring. Parent and child are independently reconstructed and evaluated
in fresh scoring processes. No old process closure, optimizer history or parent
object is available to the child's proposer. Exact float64 bytes and rule identity
are inherited through v2 artifacts; pinned source and Node remain dependencies.
This is not a strict source-reproducing quine or a hardened security sandbox.

## Controls and accounting

- **Hereditary:** the current child's coefficients propose its own successor.
- **Fixed proposer:** the original initialized rule proposes updates to the changing
  target parameters. It separates inheritance from repeated use of one optimizer.
- **Serialization only:** reconstruct parent without adopting an update. It pays
  the same probe budget, explicitly wasted, and isolates copying from improvement.
- **SPSA:** use the same scalar-derived direction with a fixed 0.1 update rate.

Each arm pays eight meta-objective calls and one learned proposal computation per
round, even if discarded. Each meta call adapts 32 tasks for six steps, with eight
scalar loss probes per step and one final loss. Thus each round charges 12,544
scalar loss calls and 1,537 transform calls per arm. Conventional-control arithmetic
is additional but measured in wall time. Initial training, parent/child evaluation
and subprocess overhead are reported separately. No cash, GPU or network needed.

The evaluator reuses v1's known-minimum rotated positive-definite quadratic oracle;
only its scalar loss is exposed to v2's operator. Sharing the task generator does
not reuse v1 populations: v2 has separately fixed seeds. All executed seeds become
exposed development data. Fresh instances remain one task family, not domains.

## First frozen development result

Lower loss is better. Each row uses a new population shared across arms.

| Generation | Hereditary child | Fixed proposer child | Serialization only | SPSA child |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1.669965 | 1.669965 | 1.622377 | 1.542775 |
| 2 | 2.278709 | 2.208049 | 1.888187 | 1.731203 |
| 3 | 2.419322 | 2.267202 | 1.956299 | 1.770024 |

The hereditary parent losses on the same respective populations were 1.622377,
1.966538 and 2.299432: **all three self-updates made adaptation worse**. Fixed
proposer also regressed, but less in generations two and three. Serialization
alone was exactly unchanged; conventional SPSA improved on its own parent in all
three rounds. Reconstruction and closure succeeded; useful heredity did not.
No repeated RSI or AGI result is established. Do not compare rows as a single
learning curve because their task populations differ.

This rules out blaming v1's explicit gradient delivery alone. A stronger next
candidate needs training for *useful self-target updates*, not just competent
updates of unrelated task weights. That would be a separately frozen training
objective, not retrospective tuning of this holdout. A fixed-proposer control
must remain: child improvement alone does not show that changing the proposer
contributes anything.

## Run

```
node projects/self_transform/self_transform_v2/test.mjs
node projects/self_transform/self_transform_v2/run.mjs .work/self-transform-v2-new.json
```

Protocol and source locks are saved before execution, refusing path reuse. Raw
receipts remain local. Focused tests cover exact bytes, invalid probes, known
quadratic directional derivatives, immutable inputs and charged budgets.
