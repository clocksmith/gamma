# Bounded source audit

The 32 frozen reference sources and both transformed arms passed the original
typed/effect replay: 2,826 cases and 106 isolated executions per arm, with zero
reference fallbacks. Independent verification regenerated the transformations
and checked all retained observations. See `qualification-summary.json`.

The syntactic reflection guard is intentionally **not a general reflection
detector or equivalence proof**. `String(functionValue)`, aliases of reflective
methods and computed property names can observe source formatting or binding
names without a literal `.toString` or `.name`. New source populations require
their own source audit, conservative rejection and fresh exact-byte replay.

For this fixed pilot, an AST inventory of every call/new target and string
literal found no eval/Function/Reflect/Object reflection route or reflective
property string. The sole direct `String` calls are in problem 1088: its numeric
limit and numeric digit/rotation array entries; they do not receive functions.
`String.fromCharCode` in 1061 constructs characters from integer codes. Other
calls target explicit local algorithms, numeric helpers, collection methods,
typed arrays, node constructors or ordinary string operations. This is a
bounded inspection of admitted sources, not a claim about arbitrary JavaScript
or adversarial callable/proxy inputs outside the pinned problem contracts.

The post-rename graph currently checks variable order, scope, neighbor sets and
reference counts, not a canonical occurrence-to-binding map. Exact-span edits,
capture constraints, AST checks and the independent finite replay support this
pilot. A future generalization should strengthen occurrence-level resolution
checking in a new version and requalify its exact output bytes; historical
contracts and receipts must not be silently changed.
