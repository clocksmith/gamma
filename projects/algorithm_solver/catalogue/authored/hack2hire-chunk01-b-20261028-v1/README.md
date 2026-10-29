# Hack2Hire chunk01-b: 16 groups, 24 variants, inferred specifications

Scope: authored, not qualified. Problem identity is the string uid `hack2hire:<variant id>`. The worklist covers
16 Hack2Hire coding groups and all 24 of their variants. Owner-delegated authoring was requested on 2026-10-28.
The sibling cohort `hack2hire-chunk01-a-20261028-v1` belongs to another author and was not touched. No Git operation.

## Specification status: inferred, not official

The local sources hold only partial, group-level previews: `payload.data.contentPreview`, `algorithmTags`,
`codingQuestions` and the title in `data/question_bank/hack2hire/details/<post id>.json`, plus the bank, description
and `reviews.json` records. No variant-specific statement, example or constraint list was available. Only Fancy
Number states a complete task and bound. Every spec, interface and domain in `contracts.json` is an **inference**
by a claude-opus-5-5 subagent on 2026-10-28. Each row records `spec_basis: inferred`, the preview fields used and the
preview `response_sha256`/`content_sha256`. Specs are paraphrased in the author's own words, and no preview text is
copied beyond short identifiers such as relationship and node-type names. `inference_uncertainty` names the guesses
for each variant. Where the source shows a provided API or a concurrent/distributed setting (BufferedFile's File sink,
the cluster workers, the binary file streams), it is modelled as a deterministic function over injected inputs, and
the spec says so.

## Method

The independent reference code, the inferred-domain validators, the contracts, the case generator and the design
were frozen before any candidate file existed (`pre-source-reference-freeze.json`). The references use subset or
ternary operation enumeration over tree nodes, mask enumeration, Python `in` substring and token checks, forward
fixpoint closures, per-query BFS, sorted runs and exact `Fraction` medians, step-bounded walks, pairwise union-find
content comparison, a linear order book, linear shopper-count search, lexicographic index combinations, Bellman-Ford
over (time, cost) pairs, outward walks, per-position `startswith` scans and repeated smallest-pair selection. No
language-agreement oracle is used. Maximum rows sit at the inferred bounds, with expected values fixed by
construction or by a linear reference.

One post-freeze amendment is recorded in the freeze file. The Directory Encryption depth bound changed from 500 to
200, because a 500-level tree nests about 1000 JSON levels and breaks Python's recursion limit in any JSON transport.
Candidates did not change.

Candidates use canonical `solve` plus a named wrapper: `Solution.<name>` in Python, or the `module.exports.<name>`
property in JavaScript. Both languages use the same algorithm and the standard library only. No input is mutated,
and all numerics are exact (JS values stay below 2^53).

The BufferedFile design variant is a real native class. Python defines it at module scope. JavaScript exposes it as
a property of the callable CommonJS `solve` export. `solve(operation_names, argument_lists)` is a separately declared
trace adapter. `native_harness.py/.cjs` (adapted from requested-22-a to string uids and a one-argument constructor)
dispatch the class directly with no solve fallback. `native_protocol.py` builds argument-only packets and checks
records on the host. `native-bindings.json` pins the unchanged easy16 transport and the judge sandbox.

## Author-local results

`test_oracles.Candidates` ran the author's own candidates against the author's own generated cases. That is self-checking
against inferred specs, not isolated or independent qualification. It also cannot show agreement with the real Hack2Hire
problems. All 7,307 rows passed in each language, and 50,771 extra seeded fuzz rows passed in both languages. Heaviest-case
CPU samples are in `checks.json`. Qualification status is `unknown` everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
node test_native_observer.cjs
```
