# Hack2Hire chunk11-a: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk11-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk10 and chunk11-b) are separate; this cohort follows the chunk09-a and chunk10-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several stop before the task or the rules: Find Matching
Skeletons (the second matching rule), Find Minimum Operations (the goal of the moves), Find Minimum Score Threshold (what is
being thresholded and the output), Find Optimal Moves (the goal), Find Path in Fibonacci Tree (labels and the query), Find Word
Path (the task after the board), Flatten 2D Array With Remove (the method list), Food Delivery System (the method list) and
Format Articles Within Width (the wrapping rules). Find Lowest Common Manager names an `Employee` object graph; the cohort
replaces it with `[name, directReports]` rows whose first row is the root. Level 2 of Food Delivery System and level 2 of
Friends by Last-K Movie Overlap have no public text at all; both are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated or aliased. Every integer stays below 2**53 (the largest are
  Fibonacci tree labels up to F(77) - 1, about 5.5 * 10**15, and Find Optimal Moves sums up to 5 * 10**13). The only
  non-integer result is an even-length median, which is a half-integer and exact in a double.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (exhaustive digit choices, manager-chain
  rescans, per-letter fill tests, full sorts, breadth-first search over move-to-end strings, per-score rescans,
  divide-and-conquer move counting, explicitly built Fibonacci trees, hop-layered relaxation, regular expressions, exhaustive
  subsets, step-by-step board walks, flat entry lists, menu rescans, character-level layout and whole-history recomputation).
  `cases.py` generates hand rows, small seeded random rows and analytic rows at the inferred maximum bounds. `test_oracles.py`
  holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every generated row,
  contract layout) plus the author-local candidate runner.
- Native classes (4 variants: Flatten 2D Array With Remove, Food Delivery System levels 1 and 2, Friends by Last-K Movie
  Overlap level 2) follow requested-22-a and chunk10-a: a module-global class (Python) or a property of the CommonJS `solve`
  export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and
  void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 14
  function variants expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Find Greatest Triple: returns an integer; leading zeros read as an ordinary number, so a three-digit pick is never worse.
- Find Lowest Common Manager: both employees are present; an employee is its own descendant.
- Find Matching Skeletons: the second rule is taken as "every dash hides the same letter of word". The stricter "the dashes
  hide every occurrence of that letter" is equally plausible and would change results. Output keeps input order and duplicates.
- Find Median In Large Array: an integer when exact, otherwise a half-integer (the chunk01-b convention).
- Find Minimum Operations: the target of the move-to-end operations is the reverse of the string.
- Find Minimum Score Threshold: a candidate is an occurring score s; s is valid when losses / games among scores >= s,
  as an IEEE double quotient, is >= threshold; return the smallest valid s or -1. This is the least certain spec in the cohort.
- Find Optimal Moves: reach arr from zeros with the fewest range increments.
- Find Path in Fibonacci Tree: order 0 empty, order 1 a single node (the LeetCode 2005 convention); pre-order 0-based labels;
  steps "U", "L", "R"; 1 <= n <= 75 so labels stay exact doubles.
- Find Path with Minimal Bottleneck: -1 when node n is unreachable within k edges.
- Find Pattern Matching Words: whole-word match; output in input order.
- Find Word Path: start on "a"; per letter "U", "L", "D", "R" runs in that order, then "!" (one fixed shortest path).
- Flatten 2D Array With Remove: `remove()` returns a boolean and is a no-op returning false when nothing is removable;
  `getVector()` keeps rows that became empty.
- Food Delivery System: delivery time is the Manhattan distance (chosen to keep times exact integers; Euclidean is equally
  plausible); the lowest price and the fastest time are independent minima; [-1, -1] when nothing qualifies. Level 2 adds
  `getBestOrder(items, x, y)` where one restaurant must offer every item.
- Format Articles Within Width: greedy fill, no padding, words never split, one empty line between articles.
- Friends by Last-K Movie Overlap: the key is the set of the last k entries; customers with fewer than k entries have no
  key. Level 1 returns groups of two or more in first-member order; level 2 streams `watch` events and answers
  `getFriends` in ascending order.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). There are no post-freeze amendments: every frozen file is unchanged. After the first run,
both Food Delivery System candidates exceeded the per-case CPU budget (level 2 took 1.38 s under python3 and 1.72 s under
node --jitless), so only the candidates were rewritten. They now use flat coordinate arrays, and level 2 caches each
distinct order's qualifying restaurants and lowest total, which is valid because the menu never changes. An order seen for the
first time still costs the frozen design's bound, O(offers of the rarest item * items).

## Local checks (author self-check, not qualification)

All 4614 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 36552 seeded Python rows matched the references. The native observers pass on all 1010 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.23 s per execution under node --jitless and 0.36 s
under python3 (Food Delivery System level 2 in both); see `checks.json`. Peak RSS was 466 MB for the whole Python candidate run
and 118 MB for node --jitless on the heaviest single rows. These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all,
the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
