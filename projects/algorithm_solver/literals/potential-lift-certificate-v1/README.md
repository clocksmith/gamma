# Item 50: fixed-potential support-budget certificate

**On each fixed 300-program cohort, no dictionary with at most 256 paid entries
and at most two one-owner entries reaches aggregate C/N <= 10%.** Here a
one-owner entry occurs in exactly one source ID; all paid entries, including
single characters, count. Entries may have any length, but complete sources and
the pinned solve-body exclusions are banned. This is a conditional full-substring
fraction bound, not an M1 or canonical-policy result.

[Accepted evidence](evidence/results.json), [generated report](evidence/REPORT.md),
[independent replay receipt](evidence/supervisor.json),
[production receipt](evidence/production-supervisor.json), [review](REVIEW.md),
[freeze and prelaunch correction](FREEZE.md).

The largest support budget with a positive bound is **k*=2 in both cohorts**.
The exact integer lower bounds are for F=10C−N, where N counts selections and
excludes Finish. All 257 budgets per cohort were independently replayed; no
budget was selected or omitted after observing the curve.

| Maximum one-owner entries k | R lower bound | Naming lower bound |
| ---: | ---: | ---: |
| 0 | 22,197 | 13,727 |
| 1 | 14,666 | 7,105 |
| 2 | 7,136 | 484 |
| 3 | −394 | −6,137 |
| 256 | −1,903,184 | −1,679,219 |

At the boundary, R's exact k2/k3 numerators are 7,135,689,484 and −394,006,905;
naming's are 483,646,210 and −6,137,009,819, all at denominator 1,000,000.
The table uses exact ceiling division. A nonpositive value is inconclusive:
three one-owner entries are not proved sufficient, nor is any larger budget.
Positivity also does not establish that the restricted class can cover the
sources at all; unique characters may make small support budgets infeasible.
Distinct-source support is not semantic reuse.

## What was certified

Retain item 28's integer occurrence multipliers exactly on every old edge. From
its backward shortest-path potentials d, assign each newly allowed occurrence
`qnew=max(0,d_i-d_j-D*b)`, with base cost b=9 for a singleton and −1 otherwise.
All new edges respect the same potential inequalities, while old tight paths
survive. The complete path term therefore remains exactly item 28's. Exact
support-class top-entry charges then give each lower bound.

The old path numerators remain 93,534,943,854 for R and 78,055,753,489 for naming.
The k0 bounds strengthen item 28's 22,196/13,725 to 22,197/13,727 because the
support restriction can reduce the old dictionary charge. The required invariant
was k0 dominance, not equality. No q optimization, witness search or source
execution occurred. The negative k256 endpoint is one fixed multiplier result;
it does not bound the full-class dual optimum from above.

| Cohort | Source characters | Full allowed entries | One-owner entries | Entries shared by at least two source IDs |
| --- | ---: | ---: | ---: | ---: |
| R | 76,107 | 13,553,771 | 13,245,477 | 308,294 |
| Naming | 76,033 | 13,561,646 | 13,270,460 | 291,186 |

Each cohort has 111,543 compressed groups and 966 exact banned occurrences.
Independent replay checked all 27,115,417 allowed depths across the two cohorts,
including all unique-entry depths, all 514 allocation rows and the exact selected
entry identities privately. It reconstructs old paths and support/weight/top
selection separately; the pinned input/parser binding and item 33 suffix index
and completeness verifier are disclosed shared dependencies.

## Execution and limits

Production completed in **6.898203 seconds** and independent replay in
**14.435679 seconds**, measured by their whole-phase supervisors. Both phases
returned two actual integer zero exits and completed cleanup. These are measured
runtimes for this run, not forecasts or universal complexity claims.

| Cohort | Production worker seconds | Replay worker seconds | Production peak RSS KiB | Replay peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| R | 6.683 | 14.287 | 465,584 | 339,316 |
| Naming | 6.205 | 13.835 | 450,256 | 327,424 |

The unchanged envelope was 600 seconds per cohort, 1,200 seconds per whole
phase, cores 6/7, one BLAS/OpenMP thread, and 8 GiB address space per process.
A single capped 10-second emergency budget governs failure cleanup/publication;
success remains inside the original phase deadline. Repeated-owner aggregation
and independent streaming retain quadratic worst-case work. All 29 execution
code pins and 20 runtime pins remain unchanged after launch.

Registered outcomes: **P1 true** (exact old path term and k0 dominance, required),
**P2 true** (some positive k>=1), **P3 false** (no positive unrestricted k256 bound).
Only the exact original item 13 source qualification receipts are reused.
There are zero fresh qualification jobs and zero new witness packets. Item 23's
later unchanged-source exit 137 remains a separate inherited failure.

No validation or cases were opened. There is no new decoding, package-cost,
canonical-action, feasible dictionary, optimality, 400/500 admission, held-out,
independent-confirmation or promotion claim. Current-best dictionaries and M1
thresholds are unchanged. Public evidence contains hashes, counts and scalar
terms, not source text, q, pools, potentials or selected-entry identities.

## Preserved proof and invented measurement

The [premeasurement design](DRAFT.md), [synthetic specification](synthetic-spec.json)
and [single measured receipt](synthetic-results.json) remain byte-for-byte
unchanged. That earlier invented run completed in 20.589095 seconds, peak RSS
489,168 KiB, with all 17 oracle tests and 514 rows agreeing. It included a paired
75,000-character fixture and a repeated-owner 12,000-character stress fixture.
Those arbitrary-q bounds are mechanism evidence, separate from this corpus
certificate. The [adapter design](DRAFT-NEXT.md) and
[report design](REPORT-DESIGN.md) preserve the prelaunch reasoning.

## 2026-10-24 interpretation update: positive support bands are coverage-infeasible

The accepted [item 56 coverage result](../support-coverage-floor-v1/README.md)
subsequently establishes a necessary one-owner-entry floor of **three in both
identical original 300-source fit cohorts**. Every positive budget in items 50
and 53 is k=0,1,2, so all of those positive fraction exclusions are **vacuous for
covering dictionaries**: those classes cannot cover the sources at all. The
recorded curves and inequalities remain valid, but the positive values exclude
no realizable covering dictionary. This supersedes the earlier uncertainty
about coverage at those budgets without changing frozen numerical evidence.

At k>=3, this floor merely stops ruling out coverage. This floor alone establishes neither 256-entry coverage
nor C/N<=10%; the fraction bounds remain nonpositive there. The
floor does not prove that three one-owner entries suffice under capacity. This
is a dated interpretation update from [independently replayed metadata](../support-coverage-floor-v1/evidence/results.json),
not a new run, changed target, promotion, or global dual-optimum claim.
