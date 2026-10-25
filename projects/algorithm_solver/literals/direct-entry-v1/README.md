# Direct-entry candidate supply

This is a candidate generator for the incremental family-vocabulary plan, **not**
a separate fit arm or a qualification result. It builds on historical
class-to-solve normalization; the new obligation is exact-byte qualification and
integration with the current source pool, not a novelty claim.

`lower.mjs` parses one complete previously qualified adapted JavaScript source.
It requires exactly one unextended `Solution` class with exactly one ordinary
nonstatic, noncomputed, synchronous nongenerator method and simple unique
identifier parameters. The complete uniform `solve(...args)` adapter must match
its expected AST exactly. Methods using `this`, `super`, `new.target`, private
names, additional Solution/solve references, or guarded reflection are rejected.
The conservative guard also rejects global reflective facilities and common
name/source/constructor/prototype/caller/stack property access. Unsupported
sources retain their existing qualified variants; rejection is not failure of
those originals.

The output is a strict `function solve(params)` containing the exact original
method-body bytes. Every external helper byte is retained verbatim; no helper is
inlined, omitted, supplied externally or hidden in a decoder. Only class/adapter
boundaries and the entry signature are replaced, with an explicit strict
directive. This preserves class-method strict call semantics for simple params.
The result is reparsed and compared with the expected AST, including literal,
regex, bigint, template and directive values. No submitted source is evaluated
by this tool.

The supported interface is ordinary judge invocation of solve with the frozen
arguments. Arbitrary external reflection on function length/source/name, class
construction or intermediate allocation is not an equivalence claim. The guard
is conservative but not a proof against all dynamically computed reflection;
source-specific audit plus exact frozen oracle/type/effect replay remain required.
No output becomes an eligible source choice from its AST-success flag alone.

Native dot must run independent typed/exact qualification of every exact emitted
byte sequence under the existing limits. Full helpers and resulting source bytes
must be charged in the downstream family vocabulary. Generic helpers that solve
a whole problem through a trivial wrapper must be excluded as whole-solution
literals even when other programs reuse them. Final held-out and protected cases
remain closed.

Run the trusted synthetic parser-only checks with the pinned Node executable and
`test_lower.mjs`. Dependency loading reuses the receipt-verified exact upstream
source loader in `role-canonical-v1/parser.mjs`.
