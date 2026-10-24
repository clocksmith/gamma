# Item 61: required-owner allocation proof

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
