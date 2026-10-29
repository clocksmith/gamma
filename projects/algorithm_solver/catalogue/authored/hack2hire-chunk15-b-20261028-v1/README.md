# Hack2Hire chunk15-b: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk15-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk14 and chunk15-a) are separate; this cohort follows the chunk14-b and chunk13-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and format strings is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Design Infinite Queue with GetRandom O(1) (every operation), Design Lazy Array (the mapped function and the rest of
the interface), Escape Room (the methods and ranking), Event Logger with Rate Limiting (the logging method), Find Restaurant
Intervals (the question itself), Find the K-th Highest Debit (what is reported), Final Values by Source Priority (the output)
and Find All 5-Minute Intervals (alignment and wrap-around). Levels 2 to 4 of Design In-memory Database with Backup and
variant 2 of Find Path in N-ary Tree have no public text at all; they are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Lazy Array
  composed maps, bounded at 1e15 by the inferred domain, and Get Total Requests and Distinct Wall Crossing sums, below 1e15);
  Find Anagram in String keys windows by four exact base-51 numbers instead of a hash.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (regex token splits, flat entry lists
  with linear search and backup replay, list removal from the front, eager array rewriting, all-pairs prefix enumeration,
  full re-sorting, print-history scans, reverse first-wins passes, minute-by-minute week walks, sorted-window comparison,
  per-start set growth, recursive searches over rebuilt child lists, per-piece seat sums, sorting of accumulated nets,
  length-4 window enumeration and whole-list rewriting). `cases.py` generates small random rows, hand rows and analytic rows
  at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a
  domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (8 variants: the four In-memory Database levels, Infinite Queue, Lazy Array, Escape Room, Event Logger)
  follow requested-22-a and chunk14-b: a module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments
  and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
  The 12 function variants expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Design File Search Tool: whole-token matches (maximal ASCII letter/digit runs) ignoring ASCII case; rows keep input file
  order; each matching line is listed once.
- Design In-memory Database with Backup: level 1 as previewed; level 2 adds `scanData` and `scanDataByPrefix` returning
  sorted `field(value)` strings; level 3 replaces the methods with timestamped ones and half-open TTL; level 4 adds `backup`
  (count of non-empty records) and `restore` (latest backup at or before the target, remaining TTL re-anchored at restore time).
- Design Infinite Queue with GetRandom O(1): `add`, `poll` (-1 when empty) and `getRandom(r)` with injected randomness, returning
  the element at position r mod size from the front.
- Design Lazy Array: `map(operation, operand)` with "add" or "multiply", changing the instance; `indexOf` returns the first index.
- Distinct Wall Crossing on Number Line: moving is free, every crossing (including re-crossing) costs the wall's cost.
- Escape Room: `advance`, `countInRoom`, `topPlayers(k)` ranked by room then by entry time; advancing from the last room is ignored.
- Event Logger with Rate Limiting: `logEvent(name, timestamp)` prints when at least `window` seconds passed since the last print.
- Final Values by Source Priority: last write wins; output is "key:value" strings sorted by key.
- Find All 5-Minute Intervals: clock-aligned multiples of 5 minutes, inclusive, wrapping past Sunday; hour without leading zero.
- Find Path in N-ary Tree: level-order serialization with null separators; variant 2 lets the path start at any node.
- Find Restaurant Intervals: maximal intervals with at least `partySize` free seats; reservations are half-open.
- Find the K-th Highest Debit: the name with the k-th largest positive net debt, ties by name, "" when there is none.
- Four-in-a-row Game: `isWinningMove(board, move, player)`, at least four, no gravity, the target cell is empty.
- Get Total Requests: one total per day, after that day's replacement.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One amendment was needed after the first candidate run: a hand-derived Lazy Array
maximum row (30000 rounds of `map add 1` then `indexOf`) expected index 2 i, but the queried target maps back to the original
value at index i (both candidates returned i). The row now expects i. References, validators, contracts and the inferred spec
are unchanged; the amendment and the old and new `cases.py` hashes are recorded in the freeze file and `case-design-summary.json`.
The first run also showed the Find Path in N-ary Tree variant 2 candidates taking 1.6 s (python3) and 3.7 s (node --jitless) on
a broom-shaped maximum row (9000 distinct leaf values below a long matching chain); both candidates now send values that do not
occur in the path straight to automaton state 0, and that row takes milliseconds.

## Local checks (author self-check, not qualification)

All 5148 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40624 seeded Python rows matched the references. The native observers pass on all 2026 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.21 s per execution under python3 (Design File
Search Tool) and 0.18 s under node --jitless (Find Anagram in String); see `checks.json`. Peak RSS was 208 MB for the whole
python3 `test_oracles.py` run and 316 MB for `test_native_observer.py`. These runs check the code against the author's own
inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above
all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
