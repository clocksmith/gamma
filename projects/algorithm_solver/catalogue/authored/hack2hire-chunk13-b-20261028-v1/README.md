# Hack2Hire chunk13-b: twenty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 21 of their variants, from coordinator
worklist h2h-chunk13-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk12 and chunk13-a) are separate; this cohort follows the chunk11-b and chunk12-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and the route and shard string
formats is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Remove Covered Point (the output), Role Privilege System (input format and precedence), Route Nearest Checkpoint
(the output), Same Word of HTML Labels (the question), Schedule Orders onto Planes (the allocation rule and output),
Sentence Variations with Anagram (the output), Shard Rebalancing (the trimming and gap rules), Shift Units Protection (the
objective), Shipping Route Cost Paths (every part and output) and Shortest Path with Gas Stations (refuelling and output).
Level 2 of Related Communities Finder, levels 2 and 3 of Segment Sequence Reconstruction and levels 2 and 3 of Shipping
Route Cost Paths have no public text at all; they are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Shift
  Units Protection totals, at most 1e14, and the scaled squared distances of Route Nearest Checkpoint, below 2e13).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (nested list scans, repeated full
  rescans, point-by-point enumeration, explicit swaps, fixed-point iteration, exact fractions, recursive string building,
  linear plane scans with copied capacities, plain recency lists, quadratic chain searches, Cartesian products, key-by-key
  coverage counts, subset enumeration, pair enumeration, Bellman-Ford relaxation, full (cell, fuel) state search, dense
  matrices and per-index sums). `cases.py` generates small random rows, hand rows and analytic rows at the inferred maximum
  bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check
  on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (2 variants: Search History System, Sparse Matrix Operation) follow requested-22-a and chunk11-b: a
  module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null (`native_protocol.py` adds the `integer[][]` return kind for the sparse matrix triples).
  `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 19 function variants expose
  `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 105 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (21 contracts, 42 implementation artifacts, 21 `source-native` design artifacts, 21 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Related Communities Finder: both lists describe the same relation; ids ordered by community index. Level 1 direct shared
  followers; level 2 the transitive closure through chains of shared followers.
- Remove Covered Point: return the remaining half-open intervals in input order, the hit interval split in place into
  non-empty pieces; idx past the last point leaves the intervals unchanged.
- Reverse Middle of Vowel Words: ASCII letters only; one-letter words unchanged.
- Role Privilege System: parallel lists (roles, parents, allowed, disallowed); a role gets its allowed list plus its parents'
  final sets, minus its disallowed list; sorted lists per role.
- Route Nearest Checkpoint: the output is the index of the nearest waypoint (smallest index on a tie), not a distance; segments
  have integer lengths and distances past the end clamp to the last waypoint, so every comparison is exact.
- Same Word of HTML Labels: true when the concatenated leaf texts (pre-order) are equal; trees are flat node lists
  `[text, children]` with node 0 as root, because nested JSON would exceed the depth cap for deep trees.
- Schedule Orders onto Planes: each item goes to the earliest-departing eligible plane with room (first fit); a rejected
  order returns [] and restores capacities; otherwise the chosen departure times per item.
- Search History System: LRU recency with most-recent-first `getTopK`, which does not count as use.
- Segment Sequence Reconstruction: level 1 a valid single chain; level 2 returns "" unless the segments form exactly one
  chain; level 3 several disjoint chains, ordered by head id.
- Sentence Variations with Anagram: list every distinct variation (original word always allowed), sorted.
- Shard Rebalancing: shards processed by (start, end, id); each keeps the suffix of its range where fewer than limit kept shards
  cover every key (dropped when empty); gaps are then filled by moving the next shard's start back; output sorted by final
  (start, end, id).
- Shift Units Protection: maximise total population of protected cities.
- Shipping Route Cost Paths: level 1 direct routes as [method, cost]; level 2 paths with at most one transfer as
  ["SRC:method:MID:method:DST", cost]; level 3 the cheapest cost with any number of transfers (0 for equal endpoints, -1
  unreachable).
- Shortest Path with Gas Stations: entering G refills to full; minimum move count or -1.
- Sparse Matrix Operation: `SparseMatrix(matrix)` from a dense list, `get`, `set` (void), and `add`/`multiply` with dense
  operands returning sorted non-zero triples `[row, col, value]` without changing the stored matrix.
- Split Array with Equal Sum: both parts non-empty; -1 when no split exists.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every frozen file is unchanged.

## Local checks (author self-check, not qualification)

All 5407 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 42751 seeded Python rows matched the references (one over-budget generated row was skipped). The native
observers pass on all 508 class cases in each language with the unchanged easy16 transport. The heaviest case takes 0.11 s per
execution under python3 (Schedule Orders onto Planes) and 0.07 s under node --jitless (Remove Covered Point); see `checks.json`. These runs
check the code against the author's own inferred contract only. Official ABI, effects, limits and correctness still need the
coordinator's isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
