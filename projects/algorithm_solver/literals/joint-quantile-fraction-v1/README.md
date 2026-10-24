# Joint fit quantiles strengthen the bound, but do not exclude 10%

[Freeze](FREEZE.md), [design](DRAFT.md), [review](REVIEW.md),
[metadata](evidence/results.json), [constraint diagnostics](evidence/quantile-diagnostics.json),
[reporting note](REPORTING-NOTE.md).

All twelve fixed points completed and independently replayed. The strongest
conditional bounds are **−23,660 for R and −23,655 for naming**, both at q=0.
They are negative and inconclusive: no feasible dictionary or impossibility
claim follows. This question is specifically the same 300 fit sources with
median selections≤32, p95≤96 and C/N≤10%; it is not a necessary condition for
the 400-program M1 population and excludes neither M1 nor a 500-program target.

Production took 119.004 seconds; independent cardinality, full-pool and assignment
replay took 207.179 seconds. Peak RSS was 361,092/358,788 KiB in production and
557,868/552,924 KiB in replay for R/naming. All twelve points complete under the
separate 1,200-second phase caps. P1/P2 true; P3 false. No restart or omitted point.


Population: the named 300 fit sources only. N counts selections excluding Finish; actions=N+1.
This report excludes neither M1 nor any 400/500-program target. No feasible witness or source qualification is produced.

All twelve fixed points completed and independently replayed.

| Cohort | q scale | Unrestricted F lower | Necessary-quantile F lower | Exact-median/p95 F lower | Excludes fixed-300 joint target |
| --- | --- | ---: | ---: | ---: | --- |
| R | 0/1 | -37980 | -23724 | -23660 | False |
| R | 1/4 | -35012 | -24353 | -24303 | False |
| R | 1/2 | -32240 | -25046 | -25009 | False |
| R | 1/1 | -27266 | -26629 | -26617 | False |
| R | 2/1 | -38023 | -37782 | -37774 | False |
| R | 4/1 | -61798 | -61723 | -61718 | False |
| naming | 0/1 | -37943 | -23719 | -23655 | False |
| naming | 1/4 | -35276 | -24522 | -24471 | False |
| naming | 1/2 | -32778 | -25386 | -25348 | False |
| naming | 1/1 | -28259 | -27305 | -27289 | False |
| naming | 2/1 | -38299 | -37868 | -37856 | False |
| naming | 4/1 | -60698 | -60511 | -60504 | False |

Nonpositive bounds are inconclusive. Conditional bounds have no reported gap to an unqualified seed encoding.

| Prediction | Outcome |
| --- | --- |
| P1 | True |
| P2 | True |
| P3 | False |


The sole minimizing median-union value is a=32 at every scale. At q=0, 283 of 285
capped programs are tight under the retained assignment in both cohorts:
148/150 lower-half, 1/1 upper-middle and 134/134 p95-remainder programs. At q=1,
211/285 R and 225/285 naming programs are tight. Uncapped programs are excluded.
Here tight means every path attaining that assigned capped optimum uses exactly
the cap number of selections; alternative optimum assignments are not enumerated.

At q=0 the exact median union adds 64 objective units beyond the necessary
three-class relaxation in both cohorts. The necessary relaxation adds 14,256/
14,224 over unrestricted paths. At q=1 those respective increases are 12.563591/
16.601542 and 637.057663/953.231842. These are exact path-numerator differences
divided by the unchanged 1,000,000 denominator, not rounded-bound subtraction.
They describe these constraints and multipliers, without causal attribution or
an independently isolated p95 effect. Auxiliary replay took 0.211 seconds and
changed no frozen file.

Item 35's q was optimized for unrestricted paths. Its unit-scale conditional
bounds −26,617/−27,289 are weaker than this experiment's q=0 bounds. The six fixed
scales do not optimize the joint dual; this negative result cannot rule out a
better joint multiplier. No upper bound or gap to quantile-infeasible seed paths
is claimed. No validation inputs, fresh qualification, private source publication,
M1 gate change or candidate replacement occurred.
