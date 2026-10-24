# Sixteen joint-dual points retain the zero-multiplier baseline

[Freeze](FREEZE.md), [design](DRAFT.md), [review](REVIEW.md),
[metadata](evidence/results.json), [synthetic measurement provenance](synthetic-spec.json).

Both cohorts completed all 16 registered points. Independent replay accepts the
retained bounds **−23,660 for R and −23,655 for naming**, unchanged from item 42's
q=0 baseline. Both earliest-best checkpoints are iteration 0. No positive bound,
feasible dictionary or joint-target exclusion follows. P1 is true; P2 and P3 are
false.

This tests one short projected trajectory, not the optimum of the joint dual.
A nonpositive result does not bound that optimum from above or show that better
multipliers cannot give a positive certificate. There was no line search, restart,
second initialization, adaptive tuning or seed-based upper bound. All 15 nonzero
search points score below q=0 in the retained diagnostic receipts.

## Independently verified scope and targets

Each cohort contains the same named 300 fit sources as item 42. The conditional
question requires median selections <=32, nearest-rank p95 <=96 and aggregate
C/N <=10%, with at most 256 paid entries. N excludes Finish; actions are N+1.
The pool contains every allowed exact substring, including singletons, one-owner
and near-whole entries, excluding global complete-source/solve-body bans. This is
a relaxation with unresolved semantic reuse, not an M1 candidate class.

| Cohort | Verified q=0 F lower | Verified final-best F lower | Best iteration | Minimizing a | Positive exclusion |
| --- | ---: | ---: | ---: | ---: | --- |
| R | -23,660 | -23,660 | 0 | 32 | No |
| naming | -23,655 | -23,655 | 0 | 32 | No |

F=10C−N. Exact numerators are −23,660,000,000 and −23,655,000,000 over the unchanged
denominator 1,000,000, so the integer lower bounds equal those exact values.
At q=0 the top-256 occurrence-weight term is zero. The sole minimizing median
case is a=32 in both cohorts. Zero and final-best q/proof hashes are identical
within each cohort, so independent replay verifies that identical pair once.
It reconstructs the full pool and bans, uses the separate segment-tree capped DP,
and checks exact assignment primal/dual or Hall receipts for all 32 median cases.
No gradient search or assignment solver is rerun by the reporter.

Even a positive bound here would exclude only this fixed-300 conditional target.
These negative bounds exclude neither M1 nor a 400/500-program target. There is
no feasible witness, primal gap, optimality, convergence or promotion claim.

## Per-step search trend

Values below are the search's exact integer numerators divided by 1,000,000,
shown to six decimal places without integer-bound rounding. **Steps 1–15 are
search diagnostics, not independently replayed trajectory certificates.** The
report checks their receipt structure, fixed steps and retained-best consistency;
only q=0/final-best receive independent mathematical replay. Selected a is 32
at every search point in both cohorts, diagnostic except at the verified target.

| Evaluated point t | R search B(q), diagnostic except t=0 | naming search B(q), diagnostic except t=0 | Registered step s_t |
| --- | ---: | ---: | ---: |
| 0 | -23660.000000 | -23655.000000 | 250000 |
| 1 | -28534.750000 | -28620.250000 | 125000 |
| 2 | -26150.500000 | -26184.000000 | 125000 |
| 3 | -24473.250000 | -24421.500000 | 125000 |
| 4 | -25818.625000 | -25880.250000 | 83333 |
| 5 | -24458.711942 | -24438.004094 | 83333 |
| 6 | -24237.414973 | -24228.290056 | 83333 |
| 7 | -24855.536669 | -24895.869835 | 83333 |
| 8 | -24094.914473 | -24072.456218 | 83333 |
| 9 | -24822.869838 | -24840.119797 | 62500 |
| 10 | -23990.142741 | -23971.705178 | 62500 |
| 11 | -24038.644695 | -24005.603015 | 62500 |
| 12 | -24214.208384 | -24347.250186 | 62500 |
| 13 | -24169.312527 | -24152.249899 | 62500 |
| 14 | -24251.187702 | -24321.125250 | 62500 |
| 15 | -24139.437567 | -24132.020749 | 62500 |

The row-15 step is recorded by the fixed rule but is not applied: 16 evaluated
points permit only 15 updates. The schedule is
`s_t=max(1,1000000//(4*ceil_sqrt(t+1)))`, with exact integer projection onto q>=0.
The supergradient is used-path occurrence counts minus selected distinct-entry
occurrence multiplicities. Both cohorts stop at `point_limit`, not a stationary
or unchanged-projection diagnostic. Objective decreases are permitted by this
finite schedule; no monotonic-ascent guarantee was assumed. Recovery from the
initial decrease still leaves all later points below the baseline.

## Full-pool and resource accounting

| Cohort | Fit source characters | Distinct allowed entries | Implicit groups | Length/bin pieces | Exact ban occurrences |
| --- | ---: | ---: | ---: | ---: | ---: |
| R | 76,107 | 13,553,771 | 111,543 | 375,160 | 966 |
| naming | 76,033 | 13,561,646 | 111,543 | 375,342 | 966 |

No source/edge truncation occurs. One program's compact endpoint table is retained
at a time; the measured peak is 195,456 bytes per cohort, below the 64 MiB cap.
The prelaunch invented fixture had 20,955 characters and maximum length 80; it was
not a corpus runtime estimate. The completed production measurements are below.

| Cohort | Production seconds | Replay seconds | Production peak RSS KiB | Replay peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| R | 525.790 | 34.329 | 347,996 | 499,808 |
| naming | 473.838 | 34.015 | 347,964 | 494,972 |

Whole production took 525.987 seconds; whole independent replay took 34.532 seconds.
Both phases complete under separate 1,200-second caps, on cores 4/5 with 8 GiB
per worker and single-thread numerical libraries. Both worker return codes are
zero in both phases. No failure receipt, missing point, partial-best acceptance,
retry or budget extension occurred.

Registered predictions: P1 (both complete and retained targets replay) true;
P2 (any strict numerator improvement over zero) false; P3 (any positive final
bound) false. Parent q was not loaded; source identities are bound to existing
public qualification hashes. No validation, private cases, new qualification,
source alternatives, protected/final-heldout inputs or training data were used.

Component intent and M1 gates remain unchanged. The public record contains scalar
metadata, timing and hashes, with no sources, vocabulary, q arrays, paths,
assignment labels or dual potentials. The finite negative trajectory supports no
claim that the joint-dual approach or full substring class is infeasible.
