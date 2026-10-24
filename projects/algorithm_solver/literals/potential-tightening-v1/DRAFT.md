# Item 53: tighten old edges under fixed path potentials

2026-10-24. Mathematical design only. No private inputs, corpus runner,
measurement, optimizer, new source execution or change to item 50.

## Target and authority

The target is the fixed-300, at-most-256-entry fraction certificate
`F = 10 C - N`, including optional paid characters and the same global source
and solve-body bans. A positive bound excludes `C/N <= 10%` only in the
specified source population and support-budget class. It does not establish
an M1 exclusion, feasibility at a larger budget, semantic reuse or a new
qualified representation. Original sources and qualification remain untouched.

Item 50 keeps item 28's exact multipliers on old edges and uses the smallest
nonnegative multiplier compatible with the old backward distances on new
edges. Item 53 asks whether removing the remaining old-edge slack strengthens
the same certificates. Its design and any eventual measurement stay separate
from item 50's already pinned implementation evidence.

## Pointwise dominance proof

Assume every old suffix distance is finite, old tight paths remain allowed,
and entry ownership and feasible selected-entry sets remain fixed.
Let `D > 0` be the integer denominator, `b(e) = 9` for a character edge and
`b(e) = -1` otherwise. For every source, let `d(i)` be the exact old suffix
distance and `d(end) = 0`. The old multiplier `q(e) >= 0` satisfies

```
d(i) <= b(e) D + q(e) + d(j).
```

Define, on **every** allowed full-substring edge,

```
q*(i,j) = max(0, d(i) - d(j) - b(i,j) D).
```

On an old edge, the inequality proves `q* <= q`; on a new edge, `q*` equals
item 50's lift. Every new edge cost is at least `d(i)-d(j)`. An old shortest
suffix path consists of tight old edges. For a tight edge its old nonnegative
multiplier equals `q*`, so that path retains exactly its old cost. Consequently
every suffix distance, and therefore the total path term `L`, is unchanged.

Each dictionary entry's activation weight is the sum of its occurrence
multipliers. Thus every entry weight under item 53 is no greater than under
item 50. For any budget `k`, the feasible selected-entry sets are unchanged:
at most 256 entries, with at most `k` entries occurring in exactly one source.
The maximum summed activation charge over those sets cannot increase.
Therefore the integer lower bound `ceil((L - T_k)/D)` cannot decrease, for
every `k = 0,...,256`, including the unrestricted endpoint.

The statement also holds for tighter fixed support classes, but those are
not added to this proposal. Absent old characters have zero occurrence weight;
their omission from the occurring full-substring universe does not change it.
Characters occurring in one source remain paid one-owner entries.

For fixed `d`, this is the componentwise smallest nonnegative multiplier
assignment making every allowed edge satisfy the same Bellman inequalities.
It consequently maximizes the fixed-`L` potential certificate among assignments
satisfying those inequalities. Among assignments preserving the actual suffix
distances `d`, it also maximizes the exact dual bound. Larger Bellman-compatible
penalties can raise actual path distances, so no optimum over that broader
family is claimed. This does **not** optimize `d`, bound the best dual
certificate from above, or imply a
strict numerical gain: lowering weights outside a maximizing set may leave
all charges unchanged.

## Evidence needed before execution

Use supplied invented DAG/string fixtures to verify exact suffix-distance
preservation, occurrence-level dominance, all 257 budget bounds, unchanged
bans, and a case with strict improvement. An independent full-depth evaluator
must agree with any optimized range aggregation. Retain a case where lowering
slack changes no top charge, so no strict-gain guarantee leaks into reporting.

Any future run must bind the original 28 fit sources, pool order, occurrence
multipliers, suffix distances and public certificate terms, plus the same
full-pool geometry and bans as item 50. Compare 50 and 53 on those identical
inputs, with all 257 budgets fixed before access. No new multiplier search,
validation, qualification cases, witness or dictionary selection is implied.
Declare fresh bounded production and separate independent-report budgets,
pin files, obtain Claude's cross-review, and preserve any incomplete result.

The algorithm-solver component intent is preserved. This changes only the
certificate construction in a proposed separate experiment; no authority,
threshold, source representation or production boundary changes.
