# Hack2Hire chunk16-b: sixteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 16 of their variants, from coordinator
worklist h2h-chunk16-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk15 and chunk16-a) are separate; this cohort follows the chunk15-b and chunk14-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound and example on 2026-10-29 from the preview, title and
tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview fields it used, the preview
`response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a paraphrase in the author's
words. No preview text beyond short identifiers, method names and format strings is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Minimize Capital Gains Tax (how sold shares are matched to purchases, and the output), Object Field Offset Manager
(every method), Pandigital Sum (the equation itself), Portfolio Value Optimization (fractional shares and output),
Product Price Query System (the queries), Product Price Tracker (the query method names), Minimum Device Procurement Cost
(the question sentence) and Number of Idle Drives (input layout). Pandigital Sum's `pattern` parameter is an author extension
so the function has an input; the official version probably takes none, and its answer would be the all-`?` count (336).

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 except the Portfolio Value
  Optimization rounding step, which uses Python int and JavaScript BigInt; Palindrome Stream Tracker uses a palindromic tree
  (exact, no hashing).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (value-set comparison at every cut,
  full re-sorting of lots, all-pairs differences, breadth-first search over coin states, a scan of every bundle count,
  zero-flow-link enumeration, per-root breadth-first search, all-robot scans, flat field lists, string reversal, permutation
  enumeration, regular-expression substitution, exact fractions, recursive top-down search, whole-log scans and dictionary
  scans). `cases.py` generates small random rows, hand rows and analytic rows at the inferred maximum bounds.
  `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every
  generated row, contract layout) plus the author-local candidate runner.
- Native classes (3 variants: Object Field Offset Manager, Palindrome Stream Tracker, Product Price Tracker) follow
  requested-22-a and chunk15-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript),
  plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 13 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 80 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (16 contracts, 32 implementation artifacts, 16 `source-native` design artifacts, 16 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Merge Values into Blocks: answer = distinct values minus the number of value-closed pieces the array can be cut into.
- Minimize Capital Gains Tax: each sell consumes the highest-priced held shares first (the heap greedy, not a global optimum
  over all matchings); 10% of each sell's positive profit; output a decimal string with one digit after the point.
- Minimum Absolute Difference Pairs: distinct values (as in LeetCode 1200); pairs [smaller, larger] in ascending order.
- Minimum Coins to Form All Amounts: unlimited copies per denomination; -1 exactly when there is no 1 coin.
- Minimum Device Procurement Cost: parameters (x, y, edgeCost, inputCost, bundleCost).
- Minimum Redistribution Cost: the cheaper of the all-clockwise and all-counterclockwise minimum flows.
- Minimum Root Edges Reversal: parameters (n, fromNodes, toNodes), since `from` cannot be a Python parameter name.
- Number of Idle Drives: neighbours anywhere on the same row or column, not only at distance 1; input as x and y lists.
- Object Field Offset Manager: `ObjectLayout(names, sizes)` with getOffset (-1), fieldAt (""), totalSize, addField
  (append, false on a duplicate) and removeField (later fields shift down).
- Palindrome Stream Tracker: case-sensitive letters and digits; the empty stream is a palindrome.
- Pandigital Sum: ABC + DEF = GHI; ordered assignments, so swapping the addends counts twice.
- Pig Latin Sentence Converter: only the two previewed rules; case kept as is.
- Portfolio Value Optimization: fractional shares, value of the bought shares only, rounded half up to two decimals as a string.
  The candidates group securities by the exact integer key floor(S * 1e8 / P), which orders distinct ratios exactly (they differ
  by at least 1e-8) and is equivalent to the cross-multiplication named in `design.json`.
- Print Folder Path Given Node ID: names joined by "/" without a leading slash; "" for an unknown id.
- Product Price Query System: `getPrices(log, queries)` with [item, date] queries; latest entry on or before the date, else -1.
- Product Price Tracker: methods `current`, `maximum`, `minimum` (as in LeetCode 2034), -1 when empty.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). The first candidate run passed every row in both languages, so no amendment was needed.

## Local checks (author self-check, not qualification)

All 4119 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 32520 seeded Python rows matched the references. The native observers pass on all 761 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.08 s per execution under python3 (Object Field
Offset Manager) and 0.17 s under node --jitless (Product Price Tracker); see `checks.json`. Peak RSS was 244 MB for the whole
python3 `test_oracles.py` run and 212 MB for `test_native_observer.py`. These runs check the code against the author's own
inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above
all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
