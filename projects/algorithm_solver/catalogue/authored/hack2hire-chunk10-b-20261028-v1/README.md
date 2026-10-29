# Hack2Hire chunk10-b: twenty-eight authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 28 of their variants, from coordinator
worklist h2h-chunk10-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk09 and chunk10-a) are separate; this cohort follows the chunk09-a and chunk08-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Find Balanced Prefix in Permutation is titled "prefix", but
its preview describes any contiguous subarray; the cohort follows the preview. Find Bad GPU Nodes is interactive (a
`TestServer.test` API); the cohort adapts it offline with a fixed halving strategy so the output, including the call count,
is defined. Several previews stop before the part that matters most: Find Eligible Order Sequence stops before the
eligibility conditions; Encode And Decode stops before the bit-packing format and the rule that chooses between run kinds;
Design an Interactive Paginator gives only the constructor and says a static render exists; Design Token Limiter names the
class but not its methods; Equalize Server Latency stops before the latency values and the goal; Financial Account Ledger
does not show the command argument layouts. Levels 2 to 4 of Design Worker Management System, Design a Task Assignment
System and Financial Account Ledger, level 2 of F1 Last Lap Improvement and levels 2 and 3 of Find Common Free Days have no
public text at all.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest the inferred
  domains allow is a level-4 salary of about 2 * 10**15; the largest in the cases is 1.5 * 10**12 for salary and
  about 5 * 10**13 for a ledger balance).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (one refill epoch at a time, full
  session/assignment/funding history rescans, per-unit salary marking, linear task-id lookups, window enumeration,
  `itertools.groupby` plus regular-expression parsing, per-position deletion, naive subtree maxima, postfix evaluation with
  fractions, exact fractions, breadth-first search over sums, split-tree counting with prefix sums, subarray enumeration,
  per-day marking, backtracking over every start airport, literal list simulation). `cases.py` generates small random rows,
  boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked
  examples, domain rejections, a domain and nesting check on every generated row, contract layout) plus the author-local
  candidate runner.
- Native classes (11 variants: TokenLimiter, WorkerManagementSystem levels 1 to 4, TaskManager levels 1 to 4, Paginator,
  Codec) follow requested-22-a and chunk09-a: a module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. Each level's class exposes only that
  level's methods. `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer
  to string uids, constructor arguments and void methods normalised to null. `test_native_observer.py/.cjs` hold
  source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 140 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (28 contracts, 56 implementation artifacts, 28 `source-native` design artifacts, 28 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Design Token Limiter: `setPolicy(userId, maxTokens, refillAmount, refillInterval, timestamp)` (void) starts a full bucket;
  refills are discrete, at policy time + k * interval, capped at the maximum; `consume` returns a boolean and removes nothing
  on failure; `getTokens` returns -1 for unknown users. Timestamps never decrease.
- Design Worker Management System: `addWorker` returns booleans (the preview quotes "true"/"false"); sessions are half-open.
  Level 2 `topNWorkers(n, position)` ranks by time in the current position, longest first, then id, formatted
  `id(time)` joined by ", ". Level 3 `promote` takes effect at the first entry at or after its start timestamp (one pending
  promotion at a time) and resets the ranking stint; `calcSalary` pays each session at the compensation in force when it
  started. Level 4 `setDoublePaid` periods are merged, so overlaps do not stack.
- Design a Task Assignment System: `getTask` returns `name(priority)` or "". Level 2 search is a case-sensitive substring
  match ordered by priority descending, then creation order. Level 3 users have a quota of active assignments; an assignment
  is active while finishTime > now; a user cannot hold the same task twice at once. Level 4 completion frees quota;
  overdue = expired without completion, in assignment order. Timestamps strictly increase.
- Design an Interactive Paginator: `next`/`prev`/`goTo` clamp and return the rendered string; the static `render` centres a
  window of visibleCount pages and prints `<`, `...`, pages with `[current]`, `...`, `>`.
- Encode And Decode: a `Codec` class. Runs of 3 or more equal values become `RLE[value, count]`; the rest is chunked into
  at most 8 values as `BP[width, v1, ..., vk]` with width = the largest bit length (at least 1).
- Equal Frequency After One Deletion allows zero deletions ("at most one").
- Equalize Server Latency: node latencies, increase only, minimum total increase (LeetCode 2673 structure).
- Evaluate JSON Expression Tree: DIVIDE truncates toward zero; every intermediate stays within 1e15.
- F1 Last Lap Improvement: integer lap times compared exactly; level 2 returns the full ranking.
- Fill Layover With Experiences returns the minimum count (or -1), not the bookings.
- Financial Account Ledger: `FUND <day> <account> <amount> <delay>` settles on day + delay; output is the BALANCE (and level-4
  PENDING) values in order, -1 for unknown accounts. Level 2 adds WITHDRAW, level 3 TRANSFER, level 4 PENDING and CANCEL
  (cancels the most recent unsettled, uncancelled funding).
- Find Bad GPU Nodes returns `[sorted bad nodes, test calls]` for the fixed left-first halving strategy.
- Find Common Free Days: level 1 lists free days within 1..totalDays; level 2 returns maximal free intervals for a large
  horizon; level 3 returns intervals where at least k of the people are free, merging each person's blocks.
- Find Complete Flight Path starts at the airport with one surplus outgoing ticket, or at the smallest airport for a cycle;
  codes are three uppercase letters.
- Find Eligible Order Sequence: an order is eligible when it exceeds its current neighbours; the smallest eligible order is
  processed first.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). There were no post-freeze amendments: the first full candidate run passed every row in
both languages. After that run, the level-4 Worker Management candidate was rewritten for constant factors only (same
merged-prefix binary-search design) because its heaviest row took 0.92 s under node --jitless; it now takes 0.65 s. All runs
recorded in `checks.json` are on the final sources.

## Local checks (author self-check, not qualification)

All 7218 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 56856 seeded Python rows matched the references. The native observers pass on all 2821 class cases in
each language with the unchanged easy16 transport. The heaviest cases take 0.66 s per execution under node --jitless (Design a
Task Assignment System level 3, 1000 sorted listings of 2000 tasks; Worker Management level 4 is 0.65 s) and 0.60 s under
python3 (Worker Management level 4, 998 salary queries over 1000 sessions and 1000 double-pay periods), see `checks.json`.
These runs check the code against the author's own inferred contract only. Official ABI, effects, limits and correctness
still need the coordinator's isolated runner and, above all, the official specifications. Qualification status is unknown
everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
