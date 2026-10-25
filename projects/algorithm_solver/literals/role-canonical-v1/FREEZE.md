# Role-canonical pilot v1 (not an M1 result)

Before any transformation or dictionary feedback, freeze these 32 development-fit
reference problems: 6, 10, 11, 15, 21, 23, 34, 42, 51, 54, 62, 64, 66, 71,
79, 84, 91, 104, 106, 115, 127, 148, 253, 347, 560, 704, 733, 1015, 1061,
1074, 1079, 1088. The exact reference hashes derive from the already independently
qualified joint-composable source pool (397 originals plus 3 mandatory successors).
This deliberately spans strings, regex, linked nodes, binary search, greedy,
backtracking, grids, DP, exact integers, observable mutation, stacks, trees, graphs,
sorting, prefix sums, union-find, and all three runtime-budget successors.

Two transformation arms: deterministic AST formatting alone; capture-safe local
binding roles plus identical formatting. No solution/algorithm replacement,
operator rewrite, loop lowering, expression rearrangement, helper extraction,
constant folding, or dictionary-cost-dependent naming occurs in this pilot.

Role prefixes: parameter `p`, catch binding `e`, declared loop index `i`, literal
array or Array constructor `a`, Map constructor `m`, Set constructor `s`, otherwise
`v`. Bindings use deterministic scope-analysis order and the first nonnegative
suffix not conflicting with live neighbor names or unresolved captured globals.
Role labels are syntactic classifications, not inferred semantic types.

The historical binding-descent capture graph is reused with its conservative
reservation of function/class names, function-valued bindings, shorthand property
bindings, global/module/class bindings and ambiguous shared AST positions.
`eval`, `Function`, `with`, and detected name/toString reflection reject both
transformation arms. Unsupported or unsafe source remains the exact reference
fallback and is counted in the 32 denominator, never silently removed.

Resolved identifier spans alone may change. Property names, strings, regex,
templates, bigint values, directives, labels, interfaces and function/class names
are invariant. Reparse the renamed source, compare its AST against the original
with only the authorized identifier edits, recheck the complete capture graph,
then reparse the printer output and compare AST structure again. Source locations
and literal raw spelling alone are excluded from structural comparison; bigint
values and regex patterns/flags are retained without JSON numeric conversion.
No parsing operation evaluates submitted source.

Each exact transformed source must next pass the original typed/exact transport,
independent frozen expected oracle and historical full effect observations under
the pinned isolated Node runtime before it becomes eligible. Parsing or finite
replay is not a universal equivalence proof. Failed transformations retain evidence
and reference fallback. Qualification is owned by the native dot execution lane.

Only after qualification: compare fresh and inherited dictionary initialization
with matched budgets and fully charged source, adapter, literals, framing and
decoder. A separate explicit fitter freeze must specify these search budgets
before fitting. No pilot validation or final protected cases are opened. The full
500 M1 denominator is unchanged; this 32-problem pilot cannot establish M1.
