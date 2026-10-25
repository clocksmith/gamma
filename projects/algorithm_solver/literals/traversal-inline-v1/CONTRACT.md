# Inlined partial-control-flow traversal variants

Fixed development-fit problems 103, 104, 107, 111 and 112 receive additional
JavaScript source alternatives. No original source, oracle, mutation/alias/type
contract or problem population changes. Freeze every complete source before its
original typed/effect replay under the existing pinned isolated runtime limits.

These sources inline the explicit DFS/state propagation already independently
qualified in traversal-family-v1, eliminating the generic helper/callback call
without hiding any code. Each complete program visibly contains its pending
stack, node pop, task-specific operation, propagated state and child pushes.
No decoder substitution, source template or runtime code generation is used.

103 and 107 collect left-before-right DFS values by depth, then perform their
respective level reversals. 104 aggregates maximum depth; 111 aggregates only
leaf depth and handles empty input separately. 112 preserves strict leaf value
comparison against the remaining target before subtracting for descendants.
The same ordinary data-tree transport restriction applies: no proxy/getter or
external source-reflection equivalence claim. Worst-case time remains O(n),
pending stack O(h), plus the required output arrays where applicable. Input
nodes are not mutated. Exact original oracle/type/effect replay is mandatory.

The shared vocabulary opportunity is explicitly PARTIAL control flow: stack
initialization, node-pop/destructuring, conditional entry, and child scheduling.
Task-specific logic lies between these shared pieces. Whole programs and whole
solve bodies remain forbidden literals; no whole generic traversal helper is
present to treat as a free primitive. Every source byte is charged.

This source-only family is not a new dictionary experiment or reset. Only after
independent exact-byte verification may its choices enter a linked supply and
local-vocabulary merge. The same 300 fit identities remain fixed. Development
validation, final 100 and protected 66 stay closed; all 500 M1 gates are unchanged.
