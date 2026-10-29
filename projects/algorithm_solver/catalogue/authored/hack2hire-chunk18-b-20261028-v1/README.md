# Hack2Hire chunk18-b: sixteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 10 Hack2Hire coding groups and all 16 of their variants, from coordinator
worklist h2h-chunk18-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk17 and chunk18-a) are separate; this cohort follows the chunk17-b and chunk16-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound and example on 2026-10-29 from the preview, title and
tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview fields it used, the preview
`response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a paraphrase in the author's
words. No preview text beyond short identifiers, method names and format strings is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Regex Pattern Matching (the question), Sum of Islands Max (the question), Data Labeling Task Scheduler (the validity
conditions), Design Durable Function Call Cache (the key requirements), Cellular Infection Spreading (the question),
Optimize Transition from Elevator to Stairs (the question) and Partition Array by Equivalence Function (the conditions on the
groups). Three groups have more than one variant and no per-variant text: Data Labeling Task Scheduler (2), Design Durable
Function Call Cache (2) and Cellular Infection Spreading (5). Their variant splits are the author's inventions, labelled
high uncertainty in each contract row.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are island sums
  up to 4e10 and stair times up to 1e12); Optimize Transition computes ceilings with an exact integer correction in JavaScript.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (alphabet stepping, per-cell column
  comparison, recursive descent, Python regular expressions, union-find, a literal least-loaded greedy, regex label parsing
  with pairwise checks, list-based LRU caches with recursive equality, day-by-day full-grid simulation, a brute-force stair
  walk per switch floor and label propagation). `cases.py` generates small random rows, hand rows and analytic rows at the
  inferred maximum bounds; four Optimize Transition rows at n = 1000 take their expected value from the unbudgeted
  independent reference (category `independent-reference-at-scale`). `test_oracles.py` holds 16 source-free tests
  (hand-worked examples, a check of the cellular analytic constructions against the reference at small sizes, domain
  rejections, a domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (2 variants: both Design Durable Function Call Cache variants, class `FunctionCallCache`) follow
  requested-22-a and chunk17-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript),
  plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 14 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 80 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (16 contracts, 32 implementation artifacts, 16 `source-native` design artifacts, 16 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Next Consonant Transformation: `transformString(s)`; y is a consonant; z becomes b.
- One-Hot Encoding of An Array: `oneHotEncode(arr)`; columns are the sorted distinct values; at most 1000 elements.
- Prefix to Postfix: `prefixToPostfix(expression)`; single-character operands (letters, digits), binary + - * / ^, valid input.
- Regex Pattern Matching: `isMatch(text, pattern)`, whole-text match; "." may appear in groups and before "*".
- Sum of Islands Max: `maxIslandSum(grid)`, 4-directional islands, the largest sum, 0 without land.
- Data Labeling Task Scheduler: variant 1 `scheduleTasks(totalTask, totalModel, totalHuman, k)` returns one canonical schedule
  (k assignments per task with distinct humans and distinct models, chosen least loaded then smallest index, which is round
  robin; [] when k exceeds either count). The official problem probably accepts any valid schedule; the canonical greedy is
  pinned only so outputs compare exactly. Variant 2 `isValidSchedule(..., schedule)` checks a schedule against the same
  inferred conditions.
- Design Durable Function Call Cache: `FunctionCallCache(capacity)` (variant 1) and `FunctionCallCache(capacity, signatures)`
  (variant 2) with `call(functionName, args, kwargs)` returning true on an LRU hit. Keys are type-sensitive (true, 1 and "1"
  differ) and ignore keyword and object key order; variant 2 also binds positional, keyword and default arguments by the
  signature. Functions cannot be passed as data, so hit/miss is the observable.
- Cellular Infection Spreading: shared rule (8 neighbours, simultaneous days, threshold 1..8); variants return the number of
  spreading days, the days until all plants are infected (-1 if never), the final grid, the grid after a given number of days,
  and every plant's infection day (-1 if never).
- Optimize Transition from Elevator to Stairs: `minimumTotalTime(n, e1, t1, e2, c)`; energy starts at 0, the minimum total time
  over feasible switch floors k.
- Partition Array by Equivalence Function: `partitionByEquivalence(nums, equivalentPairs)`; equiv is the equivalence generated
  by the pairs; groups in order of first element, elements in index order (not contiguous runs).

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). The first candidate run passed every row in both languages, so no amendment was needed.

## Local checks (author self-check, not qualification)

All 4209 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 32904 seeded Python rows matched the references. The native observers pass on all 509 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.18 s per execution under python3 and 0.12 s under
node --jitless (Data Labeling Task Scheduler variant 2, validating a 1e5-triple schedule); see `checks.json`. Peak RSS was
520 MB for the whole python3 `test_oracles.py` run and 161 MB for `test_native_observer.py`. These runs check the code against
the author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated
runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
