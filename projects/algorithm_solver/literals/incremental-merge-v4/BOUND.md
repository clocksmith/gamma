# Exact worklist pruning proof (optimizer only)

Fix a source variant x, its old vocabulary V containing all96 character entries,
and a move adding complete literal P of length L while optionally retiring old
learned parents. Any new parse with k occurrences of P becomes a valid OLD parse
by replacing each P edge with L character edges. Retired parents do not matter:
all other new edges remain in V. Therefore old_min <= new_min+k*(L-1), and
new_min >= old_min-min(occurrence_count(x,P),floor(len(x)/L))*(L-1).
Clamp at zero. If P already belongs to V, the new vocabulary is a subset of V,
so use zero addition gain instead. Overlapping occurrence counts intentionally
overestimate feasible k and thus remain optimistic.

Compute the minimum lower bound over EVERY qualified variant of each problem.
The fixed source-choice policy minimizes selection count before tie breaks, so
this bounds the selected count too. Count problems whose lower bounds exceed96
and32; these are componentwise lower bounds on the first two gate-objective
components. Only skip a move when its bound pair is lexicographically STRICTLY
worse than the best measured pair (initially the current state). Equality is never
skipped because character excess or other later terms could still improve.

Reordering the entire worklist by this pair changes no candidate, budget policy,
source choice or tie-break. The existing full candidate ranking remains unchanged.
No top-k pruning, approximate scoring, or guessed gain is used. A CPU pause before
a full surviving worklist scan still accepts no partial winner.

Draft tests exhaustively check every move's bounds on100 synthetic states,
compare bounded and full-worklist exact winners, dictionaries and source choices,
exercise full128-entry vocabularies and parent retirement, and ensure an initially
unselected variant can become best across the32-selection threshold. These finite
tests support, but do not replace, the inequality above. Submitted code is never
executed by these tests or by the optimizer.
