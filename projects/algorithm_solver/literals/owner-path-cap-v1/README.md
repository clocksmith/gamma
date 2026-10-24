# Item 57 supplied-input proof: owner path caps

This is a mathematical design with invented exhaustive checks, not a corpus
result. It keeps item 53's nonnegative occurrence penalties and path minimum
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
multiplier search, witness packet, M1 admission or promotion occurred. A separate
corpus freeze and review remain necessary. See [review record](REVIEW.md).
