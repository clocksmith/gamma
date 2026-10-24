# Item 61: required-owner allocation strengthens feasible support exclusions

The independently checked required-owner allocation excludes the 10% character
fraction for every covering dictionary with at most **9 one-owner entries for R**
or **4 for naming**, in the frozen allowed full-substring universe on each
original 300-source fit cohort. Capacity is256, singletons are paid, and the
global whole-source/solve-body bans remain. Item59's existing seed proves these
at-most classes nonempty. This is a fixed-source certificate, not M1 admission.

| Cohort | Item57 k3 bound | New k3 bound | Largest positive k: old / new | New endpoint / next bound | k256 bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| R | 6651 | 13349 | 8 / 9 | 304 / -737 | -26872 |
| naming | 119 | 6011 | 3 / 4 | 982 / -976 | -27652 |

All values bound10C-N from below. A positive value excludes the10% target;
nonpositive values are inconclusive. Budgets0–2 are coverage-empty and have
null bounds. Raw charges and integer bounds improve at29 R budgets and27 naming
budgets. The k256 charge is unchanged: required owners strengthen the small
support budgets here, not the unrestricted class. P1/P2/P3 pass; P4/P5 are false.

The [freeze](FREEZE.md) was pushed at1222ab3e7 and approved by Claude before
activation e0cf4b17e. Production and independent report accepted in4.701503 and
6.464908 supervisor seconds, respectively, both with integer exitcodes[0,0].
All120 code,23 runtime and11 public pins remained unchanged. The25 focused
checks and separate implementation audit precede execution. These are measured
observations, not a performance comparison with57's different work.

Full curves, hashes and explicit inherited/fresh flags are in
[results](evidence/results.json), with the [report](evidence/REPORT.md),
[production receipt](evidence/production-supervisor.json) and
[report receipt](evidence/report-supervisor.json). Item57's full graph proof,
potentials and caps are inherited by hash; this run freshly reconstructs56's
forced owners and every reachability recurrence, then independently recomputes
the constrained allocation. Six ancestral files per phase, eight in their
union; no q or seed file is opened. No new packets, source execution,
qualification, validation or protected input. Item13 qualification reuse and
item23's unchanged-source exit137 remain explicit. Current best stays item51.

## Earlier mathematical record


This is a mathematical proposal with tiny invented exhaustive checks, not a
corpus result or execution design. It preserves item 57's sources, penalties,
path minimum and owner caps, then requires at least one dictionary slot for
every source that cannot be segmented by all allowed shared entries.

The [proof](DRAFT.md) starts with those mandatory owner marginals, then allocates
remaining slots by descending residual concave marginal. This is exact for the
stated numerical relaxation and never weakens item 57's path-penalty bound.
Budgets below the necessary coverage floor have an explicit empty-class marker
and null numerical fields. Meeting the floor does not prove coverage feasibility.

The [tiny oracle](proof.py) shares item 57's explicit full-graph quantities;
[tests](test_proof.py) independently enumerate owner allocations, interval
schedules, every covering dictionary and every encoding path. Six focused tests
passed in 0.122 seconds. This is a development check, not a timing campaign.
Root and independent cross-review found no mathematical blocker; see
[review record](REVIEW.md).

A strict fixed-q53 example has sources `abba`, `cc`, `aa`, bans their complete
strings, and B=3. The two forced owners require at least k=2, and {a,b,c} is a
covering dictionary at that minimum support budget. The new charge is 28 versus
item 57's 38, improving the integer lower bound by 10 with the same L=72. At k=3
the charges tie again. This does not imply the bound is tight or near the target.

Other tests show no change with no forced owners or zero marginals; a budget
meeting r can still be infeasible. The forced set is derived from shared-only
reachability. Its equality with private-character ownership is specific to
item 56's accepted alphabet/ban assumptions, not a general theorem.

No private input, scalable kernel, complexity measurement, binder, runner,
source execution, fresh qualification, M1 result or current-best change.
Further implementation or execution requires a separately reviewed task.

The separate [continuation proposal](DRAFT-NEXT.md) reuses hash-bound accepted
item 57 caps and independently replays forced-owner reachability and constrained
allocation. It is design-only and grants no implementation or input access.
