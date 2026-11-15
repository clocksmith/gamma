# Training-calibrated conventional control v6

V5 improved every tested parent-to-child transition but only beat a preset
conventional rate of 0.1. V6 keeps the v5 learned mechanism unchanged and tests a
stronger conventional baseline on new seeds. No v5 result or holdout is reused.

## Calibration and fair cost boundaries

After each task-only or self-target learned initialization, calibrate a constant
conventional **meta-update rate** using separate training-support/query tasks.
There are 33 candidates: zero plus 32 logarithmically spaced rates from 0.0001 to
1.0. Evaluate three update generations per rate, minimizing mean descendant
training-query loss. This rate updates the four coefficients, not task parameters
directly. The adapted target still uses the same v5 operator and task evaluator.

Each candidate sees 16 support and 16 query tasks per generation, six task steps,
four symmetric scalar probes. Exactly the same search budget as learned
initialization is charged: 776,160 scalar losses, 95,139 transforms and 792
meta-objective calls per initializer. Every comparison arm is charged both its
learned initialization and this shared calibration, even when it discards the
chosen conventional rate. Thus each hypothetical arm pays 1,552,320 scalar losses
before evaluation. The actual runner computes shared calibration once, not four
times; unused paid computation is explicit, not a claim of equal useful training.

Every test generation still uses eight meta-objective queries, 12,544 scalar
losses and 1,537 transforms per arm. The conventional control computes and discards
a learned proposal to match that cost. It stores its scalar rate in the declared
control configuration; the model artifact still contains exactly four weights.
All artifacts, calibration rows, selected rates, raw paired losses and costs are
in local receipts. Both original initialization and added calibration sources are
hashed. No held-out data select the rate, successor, stopping point or budget.

Three fresh replicates (121000, 131000, 141000), three generations, two independent
trained initializers, 128 held-out targets per generation. Proposal/scoring workers
are fresh processes. Scalar oracle and interpreter remain external and fixed.

## Result: stronger conventional control wins

All six calibrations selected rate **1.0**, the upper search boundary. That is not
proof of an optimal rate; wider training-only search could further strengthen the
baseline. Nevertheless this calibrated baseline beat hereditary children in all
18 matched fresh comparisons. Hereditary still improved against its own parent
in all 18 comparisons. Repeated improvement alone is therefore not an optimizer
advantage or evidence that inherited modifications are necessary.

Final-generation self-target-trained results, lower is better:

| Replicate | Hereditary child | Fixed learned proposer | Tuned conventional |
| --- | ---: | ---: | ---: |
| 121000 | 0.175137104 | 0.178689864 | 0.114532497 |
| 131000 | 0.126960382 | 0.126975157 | 0.117097240 |
| 141000 | 0.078557578 | 0.078557578 | 0.078467149 |

The absolute reductions versus fixed learned proposer are 0.003552760,
0.000014775 and 0.000000000336. Mean reduction 0.001189178 is dominated by one
replicate. Against the tuned control, hereditary has *higher* loss by 0.060604607,
0.009863142 and 0.000090429 (mean deficit 0.023519392). Task-only initialization
also loses to the calibrated control in all nine comparisons.

There are only three independent initializations per training objective. Repeated
generations share ancestry; 128 targets within a cell share the trained rule.
Neither treating all tasks nor all 18 comparisons as independent replicates is
justified. The range above describes observed heterogeneity, not a population
confidence interval. The nearly zero final difference in replicate 141000 is not
meaningful evidence of an engineering advantage. No statistical superiority,
RSI, broad capability or generalization across domains is claimed.

The first run took 7.61 seconds CPU, including training, rate calibration and
isolated subprocesses. Repeating it tests determinism, not independent success.
Private receipts remain local and all prior experiments are preserved.

## Interpretation

Positive direction-constrained updates solve the gross drift seen in v2-v4 and
produce repeatable toy improvements. But a tuned fixed conventional updater is
better under this matched budget. This supports a conventional optimization
explanation, not a special hereditary advantage. The next mechanism needs to beat
this stronger baseline, not merely reproduce monotonic self-application gains.

## Run

```
node projects/self_transform_v6/test.mjs
node projects/self_transform_v6/run.mjs .work/self-transform-v6-new.json
```

Focused checks cover training-only selection, invalid rates, deterministic
calibration, zero-rate identity and equal adaptation budgets. Source/protocol
locks precede execution, and prior receipt paths cannot be overwritten.
