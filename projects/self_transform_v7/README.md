# Heredity attribution study v7

A fixed twelve-seed attribution study, **not a mechanism search**. It reuses v6's
learned positive-step operator, both initialization procedures, training-calibrated
conventional baseline and cost boundaries without changing any optimization rule.
Prior results remain unchanged. New seeds and the decision rule were saved before
execution. No seed selection, early stopping, outcome-based tuning or GPU use.

## Questions and frozen primary endpoint

1. Does changing the learned proposer each generation improve fresh-target utility
   over using the original learned proposer to update the same evolving weights?
2. Does reconstructed execution add capability beyond direct execution of the
   same artifact? Does serialization alone change behavior?

Primary: self-target-trained initializer, final generation, paired relative loss
reduction `(fixed - hereditary) / fixed` across twelve independent initializations.
Require **both** median reduction at least 1% and one-sided exact sign-test p below
0.05. Relative differences within 0.000001 count as ties and are excluded from the
sign test, not from the median. The task-only cohort, earlier generations and
conventional-control comparisons are secondary, not alternate success criteria.

Three generations and 128 fresh target instances per generation. All candidates
are frozen before scoring. Each proposal and score runs from reconstructed exact
weights in a fresh process. The same artifact/input is then executed directly
without a worker process, requiring exact output agreement. Audit computation is
recorded separately; it is not independent evidence, a free search budget or an
inference-speed claim. The direct counterpart also reconstructs the artifact, so
this tests process isolation and absence of hidden execution history, not the
speed or utility of removing the serialization operation. The serialization-only
arm separately copies weights without updating them.

## Results: prespecified criterion failed

Primary final-generation contrast:

- 8 wins, 3 losses, 1 tie.
- Exact one-sided sign p = **0.11328125**.
- Median relative loss reduction = **0.202411%**, below the required 1%.
- Mean reduction = 3.320857%, dominated by one 31.827610% outlier.
- Descriptive order-statistic interval for the median: **-0.102173% to 1.801012%**.
  This uses sorted effects 3 and 10 of 12, approximately 96.14% coverage under
  independent exchangeable replicate assumptions. It was not an additional
  acceptance rule, and the small sample does not establish broad generalization.

Both registered gates fail. A few large gains exist, but varying the learned
proposer does not demonstrate a reliable practically meaningful advantage here.
The task-only cohort's median advantage is only 0.013197%; do not substitute that
secondary outcome for the failed primary test.

The training-calibrated conventional updater has lower final loss in **all twelve**
primary comparisons. Hereditary's median relative loss deficit against it is
**21.936775%**. Its final relative deficits range from 0.051220% to 326.632650%.
These are target-loss comparisons, not percentages of intelligence or AGI progress.

Reconstruction was exact in all **288 proposals and 576 scoring runs** against
same-artifact direct execution. Serialization-only parent and child behavior was
identical. Reproduction is a useful integrity/portability property, but contributed
no measured capability beyond the inherited weights themselves.

## Costs and uncertainty

The first run took 33.04 seconds CPU, including all training, calibration, worker
processes and direct parity audits. Each arm is charged its original training and
calibration budget (1,552,320 scalar losses per initializer) and eight scalar
meta-objective calls per update. Direct parity audits double the corresponding
proposal/scoring work and have their own counters. Shared training is physically
computed once where applicable, not silently treated as free for any arm.

Independent units for the primary inference are twelve initializations, not 128
correlated tasks per trained rule or three descendants sharing ancestry. All
executed holdouts are now exposed development data. Raw artifacts, failed/negative
contrasts, local receipts and source locks are retained. No private receipts are
published; no model services or GPU jobs were touched.

## Decision

**Stop repeated heredity sweeps of this four-coefficient updater.** More selected
seeds or weaker conventional controls would not answer the failed attribution
question. This does not reject functional weight transformation or the broader
research goal. It rejects a claimed practical hereditary advantage for this
specific tested mechanism under its fixed budgets.

A next study needs a new representational hypothesis: for example, a tensor-aware
updater whose exported state represents cross-coordinate curvature or task history,
with all such state explicit and charged. It must still beat a tuned conventional
optimizer and a fixed learned proposer on separately frozen tasks. Do not call
ordinary optimizer-state persistence autonomous RSI.

## Reproduce and analyze

```
node projects/self_transform_v7/test.mjs
node projects/self_transform_v7/run.mjs .work/self-transform-v7-new.json
node projects/self_transform_v7/analyze.mjs .work/self-transform-v7-new.json
```

The analysis implements the frozen sign/median endpoint and reports all seed
contrasts. Known exact probabilities, ties, medians and invalid input are tested.
The runner verifies direct parity and records source/protocol locks before work.
