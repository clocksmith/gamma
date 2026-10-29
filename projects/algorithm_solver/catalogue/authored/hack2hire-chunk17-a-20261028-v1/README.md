# Hack2Hire chunk17-a: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk17-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk16 and chunk17-b) are separate; this cohort follows the chunk16-b and chunk15-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound and example on 2026-10-29 from the preview, title and
tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview fields it used, the preview
`response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a paraphrase in the author's
words. No preview text beyond short identifiers, method names and format strings is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Scooter Street Simulation (the question), Snowy Mountain Path with Melting (the melting rule and the question; both are
author inventions here), Thread Logs Processing (the task for both variants), Threshold Alerts (the alert rule), Thrilling
Teleporters (the question for both variants), String Tokenization (rules after longest match), URL Query Parameter Parsing
(rules after key=value) and Roadway Segment Speed Query (the method list). Randomly Partition Array and Typed Task Lock are
inherently nondeterministic upstream; here randomness is injected as an explicit `randomInts` list and concurrency is
modelled as a deterministic single-threaded call trace with FIFO admission.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53. The one float result
  (Roadway Segment Speed Query `getAverageSpeed`) is a single correctly rounded division of exact integers in both languages.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (index-permutation replay, subset
  enumeration, report scans with exact fractions, unit-step simulation, recursive descent, permutation enumeration,
  whole-history replay, repeated selection, all-key comparison, direct window counts, suffix scans, bucket insertion,
  timestamp lists, regular-expression parsing, Bellman-Ford style relaxation and list rescans). `cases.py` generates small
  random rows, hand rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 20 source-free tests
  (hand-worked examples, domain rejections, a domain and nesting check on every generated row, contract layout) plus the
  author-local candidate runner. `oracles.FLOATS` marks the variant whose JavaScript float results compare by numeric value,
  since JavaScript cannot tag an integral float; Python must return `float`.
- Native classes (3 variants: Roadway Segment Speed Query, Stock Trade Ranking System, Typed Task Lock) follow
  requested-22-a and chunk16-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript),
  plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null; `native_protocol.py` adds the `float` return kind and the numeric-value comparison for JavaScript floats.
  `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 15 function variants expose
  `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Randomly Partition Array: `randomPartition(nums, k, randomInts)`; Fisher-Yates from the back with swap index r mod (i + 1),
  then k consecutive blocks.
- Reduce Gifts: remove the most expensive items until the k largest remaining fit the threshold or fewer than k remain.
- Roadway Segment Speed Query: `addReport`, `removeReport` (by exact (start, end, speed), boolean) and `getAverageSpeed`
  (float mean, -1.0 when uncovered); integer positions 0 to 1e6.
- Scooter Street Simulation: minimum walking distance when a passed scooter may always be taken (union of 10-unit ride segments).
- Simplify Expression: every term kept in order with its effective sign; no combining of like terms; unary minus only at a group start.
- Snowy Mountain Path with Melting: each day snow falls, then min(melt, depth) melts; answer per day is the total ascent from
  point 0 to n - 1. This question is an author invention.
- Stock Trade Ranking System: `getRankedStocks()` returns every name by total descending, ties by name ascending.
- String Tokenization: returns ids; an unmatched character is output as itself.
- Thread Logs Processing: variant 1 orders entries by (processId, threadId, timestamp); variant 2 returns
  "pid:tid:count:first:last" per thread.
- Threshold Alerts: alert when the window average is at least the threshold (as LeetCode 1343); returns the count.
- Thrilling Teleporters: variant 1 returns the sorted distinct end squares of one turn; variant 2 the fewest turns from
  square 0 to lastSquare (any roll may be chosen), or -1.
- Typed Task Lock: `acquire(jobId, jobType)` returns whether the job runs at once; `release(jobId)` returns the ids admitted.
  New jobs never overtake waiting ones.
- URL Query Parameter Parsing: a key without "=" maps to ""; empty pieces and empty keys are skipped; a repeated key maps to
  the list of its values; no percent-decoding.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). The first candidate run passed every row in both languages. Two amendments followed,
both recorded with hashes in the freeze file: `cases.py` shrank two Stock Trade Ranking System analytic rows to lower peak
memory (524 MB before), and the Roadway Segment Speed Query `comparison` field in `contracts.json` now states the float rule
the frozen tests already applied.

## Local checks (author self-check, not qualification)

All 4637 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 36560 seeded Python rows matched the references. The native observers pass on all 760 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.16 s per execution under python3 (Roadway
Segment Speed Query) and 0.13 s under node --jitless (Thread Logs Processing variant 1); see `checks.json`. Peak RSS was
277 MB for the whole python3 `test_oracles.py` run and 290 MB for `test_native_observer.py`. These runs check the code
against the author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's
isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
