# Owner path caps exclude 10% in nonempty support classes

The independently checked original-fit run gives **10C−N >= 6,651 for R and
>=119 for naming at k=3**, where k bounds the number of dictionary entries
occurring in only one source. Item59 established that these capacity256 classes
are nonempty. This is the first nonvacuous fraction exclusion in the recorded
full-substring classes permitting one-owner entries. The class retains the frozen
global whole-source/solve-body bans and paid singleton entries; there is no free
character fallback.

| Original300 fit cohort | Item53 k3 bound | Item57 k3 bound | Largest positive k | Last positive bound | Next bound | Unrestricted k256 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R | -393 | 6,651 | 8 | 581 | -425 at9 | -26,872 |
| naming | -6,137 | 119 | 3 | 119 | -1,188 at4 | -27,652 |

Thus C/N<=10% is excluded for every covering dictionary in this allowed class
with at most256 entries
and at most8 one-owner entries on original R, and at most3 on original naming.
The naming margin is small:119 at k3, with a negative bound already at k4.
The at-most-k classes from3 onward are nonempty by the existing seeds in
[item59](../support-budget-feasibility-v1/README.md). Positive budgets0–2 still
have no covering dictionaries. Larger budgets remain inconclusive; this is no
unrestricted10% impossibility, optimized-potential claim, new dictionary or M1
qualification. Source rewriting changes the target and is outside this bound.

The [complete report](evidence/REPORT.md) and [all257 paired rows per cohort](evidence/results.json)
retain item53, exact charge reductions, work and commitments. Both cohorts
improve255 of257 raw and integer budgets. At k256, R improves by1,876,312 integer
units and naming by1,651,567, while both bounds remain negative. Predictions
P1–P4 pass; P5 (positive unrestricted endpoint) fails.

Production supervisor elapsed10.439110 seconds; separate independent report
supervisor elapsed48.446613 seconds, both with exits[0,0] and completed cleanup.
All81 code/23 runtime pins remain unchanged. Every production forward recurrence
and independent backward schedule, owner top list and budget row agrees, and
both historical50/53 proofs are exactly reconstructed. Per-worker report peaks
are684,632/663,332KiB for R/naming; these are process peaks, not aggregate memory.

There were no validation/case reads, source executions, new qualification jobs
or witness packets. Exact original13 qualification is reused, with item23's
later unchanged-source exit137 preserved separately. Currentbest51flat and M1
thresholds are unchanged. See [review](REVIEW.md) for identities and boundaries.

## Earlier invented evidence

The initial mathematical design used invented exhaustive checks, before the
original-fit result above. It keeps item 53's nonnegative occurrence penalties and path minimum
fixed, and caps each owner's one-owner penalty contribution by the maximum
weight of a nonoverlapping interval schedule. Shared penalties keep their old
occurrence-sum upper bound.

The [proof](DRAFT.md) shows that capped owner prefixes are discrete concave,
that stable marginal allocation is exact for the numerical relaxation, and
that the resulting lower bound never weakens the old support-class bound.
Top B entry weights per owner suffice for allocation. The interval schedule
must still consider every allowed one-owner occurrence.

The [supplied-input oracle](proof.py) and [tests](test_proof.py) cover strict gains
from cross-entry and repeated-occurrence overlap, unchanged nonoverlap charges,
shared singletons, caps, zero/tied weights, and corruption rejection. Independent
enumeration checks every tiny covering dictionary and encoding path, interval
subset and integer owner allocation. Five focused tests passed in 0.092 seconds;
this is development validation, not a complexity measurement.

At the initial proof stage there were no private inputs, multiplier optimization,
witness, execution contract or launch. The explicit oracle materializes the tiny
full substring graph and is not a scalable production implementation. Any later implementation must justify its
full-graph scheduling calculation and receive a separate freeze and review.

## Accepted invented measurement

The single reviewed measurement at commit `e51880108` completed under the
[fixed synthetic protocol](SYNTHETIC-SPEC.md) and
[specification](synthetic-spec.json). Both exact item 53 invented fixtures were
retained. [Results and complete curves](synthetic-results.json) and the
[supervisor receipt](synthetic-supervisor.json) are complete with integer exit 0.
All 35 code and 12 runtime pins remained unchanged after execution.

Whole-run elapsed was 26.868267 seconds; supervisor receipt elapsed was
26.868342 seconds. All 15 mathematical/production/checker tests passed before
fixture work (0.544055 seconds). Cumulative worker peak was 617,256 KiB;
supervisor peak was 31,420 KiB. These are separate process peaks, not aggregate
memory. No matched historical timing ratio or corpus runtime estimate follows.

| Invented fixture | Production seconds | Independent seconds | Strict raw-charge / integer-bound budgets | Largest positive k: 53 → 57 |
| --- | ---: | ---: | ---: | ---: |
| paired_prefix_75k | 4.790766 | 15.452147 | 255 / 255 | 75 → 81 |
| repeated_one_owner_12k | 2.186949 | 2.845463 | 256 / 256 | 0 → 4 |

| k | Paired 53 | Paired 57 | Repeated-owner 53 | Repeated-owner 57 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 65,775 | 65,775 | 94,466 | 94,466 |
| 1 | 64,886 | 64,886 | -364,326 | 72,392 |
| 2 | 63,999 | 64,011 | -822,975 | 50,380 |
| 3 | 63,115 | 63,143 | -1,281,482 | 28,459 |
| 256 | -70,454 | -57,362 | -116,365,267 | -151,368 |

The table contains integer lower bounds for the invented fixed-source classes.
The unrestricted endpoint remains nonpositive for both fixtures. Gains do not
prove that a class covers its sources or contains a feasible dictionary.

All 257 item 57 rows, per-owner top identities/counts/prefixes/caps, allocation
choices and shared prefixes agree independently. Both paired item 50/53 proofs
and the saved item 53 curves/digests match exactly. Every production forward
schedule recurrence was checked from independently replayed potentials and fresh
AC ownership/bans: 75,000 and 12,000 positions, respectively. Each backward
schedule scanned all possible endpoints too, including entries omitted from
owner tops. The paired fixture retained 76,800 owner-top entries and inspected
9,412,500 endpoints per schedule traversal; the repeated fixture retained 3,072
entries and inspected 6,006,000 endpoints per traversal.

This supplies correctness evidence on the tested inputs and one bounded
complexity observation only. No private corpus, source execution, fresh qualification,
multiplier search, witness packet, M1 admission or promotion occurred. The later corpus freeze and review are recorded above. See [review record](REVIEW.md).
