# Occurrence-checked binding alignment — prepared, not qualified

Research-only successor to `literals/role-canonical-v1`. The three owner modules
`parser.mjs`, `bindings.mjs`, and `canonicalize.mjs` are exact unchanged tracked
copies, hash-bound in PREPARATION.json. No parallel parser, registry, or solver.
Upstream source parser receipt is dd550ff8cb1966e56c0b2fc4a56e376d4f71ceb3175222300eb6ccfc71766365
(46 immutable files). The older gamma-parser-runtime blocked receipt is not used.

`alignment.mjs` strengthens the old count/neighbor graph check with stable AST
structural paths for every declaration and reference, each resolved binding slot,
reference read/write/init flags, scope/upper/block identities, and exact unresolved
global names. Compare before and after exact-span renaming AND printing. This
rejects exchanged references even if reference counts and neighbor sets match.
Existing capture graph and structural AST checks remain unchanged.

First static subset is deliberately narrow: no calls/new, function values,
reflection/ambient names, templates, string/regex values, getters/setters,
callbacks/classes, spread/rest or non-length named property access. Numeric array
indexing is only a candidate for admission: independent exact-source review MUST
establish numeric bindings and JSON numeric/boolean/null-array input domain with
no callable/proxy/accessor inputs. The syntactic check alone grants nothing.
Source SHA256 is recomputed from actual bytes and must match the supplied reviewed
audit. Global/module/function names, properties, strings, entrypoint and API names
are not renamed. Closure/shadowing handling uses the existing scope engine; names
are not simply shortened. The initial names are the owner's role labels, not a
new dictionary search.

17 independently authored public synthetic parser controls are prepared in
synthetic-probe.mjs. Source strings are parsed, NEVER evaluated. No JS was run by
the author. Execute this trusted probe only in a separately approved pinned native
runtime, with the immutable parser dependency closure mounted as inert code.
`verify_synthetic.py STDOUT` is the host-only verifier. Controls cover exact alpha
mapping, shadowing, closure capture, swapped-reference/capture errors, unresolved
global identity, strict-subset rejection and audit/hash guards. Native process
success and transport completeness must also be independently checked.

No current875 source or old32 pilot payload is read by this owner. In particular,
closed66 remains closed. After synthetic approval, sample only existing current
fit875 metadata/live-gated IDs, independently admit a small source-specific subset,
keep original qualified alternatives and denominator fixed, and freeze new exact
bytes/provenance in separate private paths. Fresh original effects/equivalence
replay is required before any transformed alternative becomes eligible. Pricing
must compare N AND absolute singleton C, source choices, all literal/package costs,
and exact full300 decoded paths. Unsupported sources retain original fallback.
No promotion or M1 assertion. No new fit/global search has run.

All files here are code, public synthetic fixtures, or hashes. No corpus source,
literal dictionary, packets, private cases, or runtime output. This subtree is
NOT included in the previously reviewed PUBLIC-CHECKPOINT-v2 allowlist.
