# Hack2Hire chunk11-b: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk11-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk10 and chunk11-a) are separate; this cohort follows the chunk09-a and chunk10-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names, request formats and the keypad
mapping is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Friendship and Balance Tracker (only REGISTER and FRIEND_REQUEST are visible), Fuel Station Queue Simulation (output
and timing), Generate Unique Usernames (the construction rule), Gift Delivery Scheduler (the output), Hopscotch (start,
target and output), Incremental Task Scheduler (every operation), Jumping by Height (jump length, height update and output),
KV Store with Prefix Search (the prefix method) and Largest Group of Mutual Strangers (the conditions on the relationships).
Levels 2 to 4 of Implement Dataset Join Operation and level 2 of Largest Rectangle Area have no public text at all; they are
inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Friendship
  and Balance Tracker balances, at most 1e14 in principle, and Fuel Station waiting times up to about 1e9).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (linear list searches, a second-by-second
  clock, augmenting-path flow, Bellman-Ford relaxation, binary-string prefix scans, nested-loop joins, full rescans for the
  task order and cycle check, eager filtering, step-capped walks, sort-every-query, memoised suffix sets, set intersection,
  subset enumeration, per-window sorts, pair and triple enumeration). `cases.py` generates small random rows, hand rows and
  analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain
  rejections, a domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (3 variants: Incremental Task Scheduler, Iterator with Filter, KV Store with Prefix Search) follow
  requested-22-a, chunk09-a and chunk10-a: a module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and
  void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The
  17 function variants expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Friendship and Balance Tracker: one response per request, "OK" or "ERROR"; added request types
  `v1/ACCEPT_FRIEND_REQUEST/{seq}`, `v1/TRANSFER/{from}/{to}/{amount}` (friends only, no overdraft) and `v1/BALANCE/{user}`
  (decimal balance).
- Fuel Station Queue Simulation: one second per liter, strict queue order, first free dispenser in X, Y, Z order; return the
  longest wait, or -1 when a car can never be served.
- Generate Unique Usernames: given-name initial plus family name, lowercased, cut to 8; duplicates get the smallest unused
  numeric suffix with the base shortened to fit 8 characters.
- Gift Delivery Scheduler: whole-hour slots 9 to 16, at most n per slot; return the maximum number of recipients served.
- Hopscotch: minimum number of moves from `start` to the last cell, -1 when unreachable or the start is an obstacle.
- IP Routing Lookup: longest-prefix match, last listed wins on identical prefixes, "" when nothing matches.
- Implement Dataset Join Operation: the output includes a combined header and keeps both copies of the key column; level 1 inner,
  level 2 left (empty padding), level 3 full outer (unmatched processor rows last), level 4 inner on a composite key list.
- Incremental Task Scheduler: `addTask(id, dependencies)` rejects duplicates and cycles and accepts not-yet-added prerequisites;
  `getExecutionOrder()` lists only runnable tasks, smallest id first among ready ones.
- Iterator with Filter: the filter is a name (even, odd, positive, negative, nonzero), because a callable cannot travel in JSON;
  `next` is only called when an element remains.
- Jumping by Height: a jump moves exactly currentHeight cells, the height becomes the landing value, directions alternate
  starting left; return the number of jumps before leaving the array, or -1 for an endless walk.
- KV Store with Prefix Search: the preview's thrown errors are excluded from the domain (set only new keys, update only present
  keys); `prefixSearch(prefix)` returns values ordered by key.
- Keypad Letter Combination: runs of a digit split into groups of 1 up to the letter count; all results sorted; "" gives [].
- Largest Common BST Value: LeetCode level-order arrays with distinct values per tree.
- Largest Group of Mutual Strangers: the hidden conditions are taken to make the graph a forest (maximum independent set).
- Largest K Elements in Sliding Window: each window's k largest in descending order, duplicates kept.
- Largest Rectangle Area: level 1 axis-aligned, level 2 any orientation (area is an exact integer); 0 when none exists.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every frozen file is unchanged.

## Local checks (author self-check, not qualification)

All 5126 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40584 seeded Python rows matched the references. The native observers pass on all 759 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.44 s per execution under node --jitless (KV Store with
Prefix Search) and 0.34 s under python3 (same variant); see `checks.json`. These runs check the code against the author's own
inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above
all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
