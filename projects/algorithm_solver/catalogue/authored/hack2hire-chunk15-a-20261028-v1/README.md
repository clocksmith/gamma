# Hack2Hire chunk15-a: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk15-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk14 and chunk15-b) are separate; this cohort follows the chunk14-b and chunk13-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers and method or field names is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Closest Pair of Points cites LeetCode 973 (K Closest Points
to Origin) as its relative, but its own text asks for the minimum distance between two points, which matches the title. Several
previews stop before the rule that decides the answer: Bulk Fruit Order Discount (prices, tier rule and output), Campground Carpool
(the question itself), Car Fleet Scheduler (the assignment rules), Count Intervals Covering Point (the method names), Crypto Order
Matching (the sell rule, processing and output), Datapoint Window Sum by Tag (what is computed), Dependency Version Check (the API
method), Design Article System (the flip and ranking methods) and Design Connect Four II (any method after `drop`). The second
variants of Car Fleet Scheduler, Datapoint Window Sum by Tag, Dependency Version Check and Design Connect Four II have no public
text at all; they are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Count Days
  for Scheduled Tasks day numbers, about 1e14, and Bulk Fruit Order Discount and window sums, at most 1e14); JavaScript integer
  division uses `(a - a % b) / b`. Closest Pair of Points returns the correctly rounded square root of an exact integer squared
  distance, which Python `math.sqrt` and JavaScript `Math.sqrt` compute identically.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (exhaustive ordered selections, pairwise
  connected components, repeated road scans, linear car scans, window sorting, all-pairs distances, path-keyed dictionaries,
  day-by-day simulation, per-query interval scans, enumeration of question marks, linear book scans, window rescans, rebuilt
  arrays, linear and minimum scans, full replays with sorting, and column-stack rendering with whole-board rescans). `cases.py`
  generates small random rows, hand rows and analytic rows at the inferred maximum bounds (Count Days for Scheduled Tasks
  maxima use a third, divisor-block counting method). `test_oracles.py` holds 19 source-free tests (hand-worked examples,
  domain rejections, a domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (4 variants: Count Intervals Covering Point, Design Article System, both Design Connect Four II variants) follow
  requested-22-a and chunk14-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a
  separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 16 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Build Longest Palindrome: all words share one length, so the answer pairs each word with its reverse around at most one
  palindromic middle word.
- Bulk Fruit Order Discount: orders of one fruit chain into a group while consecutive timestamps differ by at most 600000;
  inputs add `prices` ([fruit, unit price]) and `tiers` ([minimum quantity, discount percent]); groups of two or more orders take
  the tier with the largest threshold not above their quantity; cost per group is floored; the answer is the total.
- Campground Carpool: each friend rides with the driver who passes their home first (driver 1 on a tie); output is two name lists
  in pickup order.
- Car Fleet Scheduler: reservations are processed by start (ties by input index) and take the smallest free 1-based car id; level 1
  adds cars as needed, level 2 has a fixed fleet and gives -1 to reservations that find no free car.
- Check Prefix Permutation: a boolean list.
- Closest Pair of Points: integer coordinates, pairwise different points, float result (see checks.json for the JavaScript
  number comparison).
- Copy Neighbor Sums Between Binary Trees: LeetCode level-order lists in and out, trailing nulls trimmed; created nodes start at 0.
- Count Days for Scheduled Tasks: task i runs on days 1, 1 + intervals[i], ...
- Count Intervals Covering Point: `IntervalCounter(intervals)` with `count(x)`.
- Count Valid Binary Combinations: maximal runs of "1" in left-to-right order must equal `arr`.
- Crypto Order Matching: incoming `[side, price]` orders against resting books; a buy takes the lowest sell at or below its
  price, a sell the highest buy at or above it; unmatched orders rest; output is the matched price or -1 per order.
- Datapoint Window Sum by Tag: datapoints are objects sorted by strictly increasing timestamp; level 1 sums tagged values in the
  time window [t - k + 1, t], level 2 sums the last k tagged values.
- Delete k Elements to Balance: an empty remainder is balanced.
- Dependency Version Check: the API is replaced by a parallel boolean list (call counts are not checked); level 1 has sorted
  versions, level 2 unsorted versions compared numerically per component; null when no version has the feature.
- Design Article System: adds `downvoteArticle`, `getRecentFlips(userId, k)` and `getTopArticles(k)`, both returning article
  names; ranking ties go to the smaller id; a first vote is not a flip.
- Design Connect Four II: row 0 is the top row; cells are one-character strings; level 2 adds `getWinner()`, which reports the
  first color to complete four in a line, or "0", and never changes afterwards.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One amendment was needed after the first candidate run: a hand-derived Check Prefix
Permutation maximum row (odd values ascending, then even values ascending, n = 200000) expected true only for k = 1 and k = n,
but values 1..n - 1 fill every position except the last, so k = n - 1 is also true. Both candidates returned that, and the
independent reference gives the same pattern at n = 8 and n = 10. The row now expects true for k in {1, n - 1, n}. References,
validators, contracts and the inferred spec are unchanged; the old and new `cases.py` hashes are recorded in the freeze file
and `case-design-summary.json`.

## Local checks (author self-check, not qualification)

All 5181 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40824 seeded Python rows matched the references. The native observers pass on all 1020 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.18 s per execution under python3 (Design Article
System) and 0.23 s under node --jitless (Car Fleet Scheduler level 2); see `checks.json`. Peak RSS was 390 MB for the whole
python3 `test_oracles.py` run and 540 MB for the whole python3 `test_native_observer.py` run. These runs check the code against
the author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated
runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
