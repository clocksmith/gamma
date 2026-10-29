# Hack2Hire chunk17-b: sixteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 16 of their variants, from coordinator
worklist h2h-chunk17-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk16 and chunk17-a) are separate; this cohort follows the chunk16-b and chunk15-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound and example on 2026-10-29 from the preview, title and
tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview fields it used, the preview
`response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a paraphrase in the author's
words. No preview text beyond short identifiers, method names and format strings is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Write Disk Block With Cycle (the interface and any further operations), Alien Base Attack (the operations), Array
Generation Service (the operations and the goal), Bring Servers Down (the attack rule), Cross-Day User Trust Scoring (the
trust-score methods), Evaluate String Expression II (the syntax), Find Frequent Events in 24 Hours (the whole question), Find
Peak Event Moment (the output), Find Redundant Substring (the question) and URL Router Design (tie rules after "fewest
wildcards"). Cross-Day User Trust Scoring covers only the previewed `crossDayDiverseUsers` method; the trust-score methods
the title promises are not specified or implemented here.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (Evaluate String Expression II
  keeps every intermediate value within 2**53 - 1 by its inferred domain, and its JavaScript result never returns -0).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (full route scans, index-pair dynamic
  programming, a prefix dynamic-programming table, all-pairs position checks, per-write block scans, per-query segment checks,
  step-by-step simulation, subset dynamic programming, triple loops, per-call log rescans, recursive descent, per-row window
  counts, exhaustive path enumeration, per-entry attendance counts, direct substring checks and per-ticket filling).
  `cases.py` generates small random rows, hand rows and analytic rows at the inferred maximum bounds.
  `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every
  generated row, contract layout) plus the author-local candidate runner.
- Native classes (4 variants: URL Router Design, Write Disk Block With Cycle, Alien Base Attack, Cross-Day User Trust Scoring)
  follow requested-22-a and chunk16-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript),
  plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 12 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 80 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (16 contracts, 32 implementation artifacts, 16 `source-native` design artifacts, 16 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- URL Router Design: `Router()` with `addRoute(pattern, handler)` (re-adding a pattern replaces its handler) and
  `callRoute(path)`; "*" matches one segment; fewest wildcards, then a literal beats "*" at the leftmost differing segment; "".
- Unequal Elements: `maximumLength(elements, k)`, at most k adjacent unequal pairs in the subsequence.
- Wildcard Matching: only "*" (no "?"), whole-string match.
- Word Pattern Match: `matchWords(pattern, words)` returns one boolean per word; character-level bijection; different length is false.
- Write Disk Block With Cycle: `DiskBlockManager(n, maximumCycles)` with `write()` returning the chosen block id, -1 when all are worn out.
- Alien Base Attack: `AlienBaseAttack(n)` with `attack(x)` (integer x; outside the base it does nothing) and `isDestroyed()`.
- Array Generation Service: `getMaximumArray(arr, state, m)`; m operations, an available element may be reused, a blocked index
  unblocks when its left neighbour was available; the lexicographically largest S.
- Bring Servers Down: `getMinRequests(request, health, k)`; per round every live server handles its requests, then one live server
  loses k health; minimise total handled requests (weighted completion time, Smith's rule).
- Count Reversing Triples: strictly decreasing index triples.
- Cross-Day User Trust Scoring: only `crossDayDiverseUsers()`; users present on both days with at least two order types overall.
- Evaluate String Expression II: prefix form `(add e1 e2 ...)` / `(mul ...)`, at least two arguments, signed literals.
- Find Frequent Events in 24 Hours: `findFrequentEvents(logs, k)` returns the sorted event types that one user performed at least
  k times with a timestamp span below 86400 seconds.
- Find Longest Path in DAG: longest by edge count, lexicographically smallest node list on ties, [] for no edges.
- Find Peak Event Moment: the earliest integer time with the maximum number of guests present ([entry, exit) presence).
- Find Redundant Substring: substrings counted by position; vowels a, e, i, o, u.
- Garage Occupancy per Timestamp: `getOccupancy(n, tickets)`, a car counts from entry through exit inclusive.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). Two post-freeze amendments are recorded there with before and after hashes: one Word
Pattern Match analytic row listed 250 expected values for 200 words (author arithmetic; corrected to 100 true and 100 false,
which the candidates and the independent reference agree on), and the URL Router Design inferred call bound was lowered from
2e4 to 1e4 calls after the first run measured 0.74 CPU s in python3 on the adversarial trace, with its maximum rows scaled to
match. No reference algorithm changed.

## Local checks (author self-check, not qualification)

All 4126 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 32472 seeded Python rows matched the references. The native observers pass on all 1018 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.38 s per execution under python3 and 0.34 s under
node --jitless (URL Router Design, a trace where every wildcard prefix fails at the last segment; Write Disk Block With Cycle
is 0.34 s under node --jitless); see `checks.json`. Peak RSS was 313 MB for the whole python3 `test_oracles.py` run and
350 MB for `test_native_observer.py`. These runs check the code against the author's own inferred contract only. Official
ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the official
specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
