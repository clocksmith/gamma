# Hack2Hire chunk10-a: thirty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 31 of their variants, from coordinator
worklist h2h-chunk10-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk09 and chunk10-b) are separate; this cohort follows the chunk08-a and chunk09-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Design Delayed Tasks Scheduler describes a real-time,
multi-threaded scheduler that prints messages; it is modelled with a caller-supplied clock and returned values so the
behaviour can be checked. Design Cache with Eviction is tagged CONCURRENCY; thread safety is not observable in single-threaded
traces and is not modelled. Design Persistent Key-Value Store names a provided `Medium` interface; the cohort replaces it with
`save()` returning and `load(blob)` taking the byte list. Many previews stop before the methods or rules: Temporal Key-Value
Store, Cache with Eviction, ChatBot System (the three bot types), In-Memory SQL (everything after `createTable`), KV Store with
Rollback (everything after `set`), Note-Taking System, Persistent Key-Value Store, Query Pagination (page parameters and
order), Ring Buffer (method signatures) and Squirrel Nut Tracker (hide and retrieve rules). Every level above 1 of a
multi-variant group has no public text at all; those levels are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated or aliased. Every integer stays below 2**53 (the largest
  are Squirrel Nut Tracker prefix sums up to about 2 * 10**14 and Query Pagination amounts up to about 10**11 cents).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (explicit-comparator insertion sorts,
  event-list rescans, linear minimum scans instead of heaps, snapshot stacks for transactions, sort-everything-per-query,
  explicit byte encoders, per-level nut simulation, stream index arithmetic for the ring buffer). `cases.py` generates small
  random rows, hand rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests
  (hand-worked examples, domain rejections, a domain and nesting check on every generated row, contract layout) plus the
  author-local candidate runner.
- Native classes (26 variants) follow requested-22-a and chunk09-a: a module-global class (Python) or a property of the
  CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter.
  `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids,
  constructor arguments and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls
  plus author-local runs. The five function variants (Custom String Sorting, Card Game III levels 1 to 3, Query Pagination)
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 155 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (31 contracts, 62 implementation artifacts, 31 `source-native` design artifacts, 31 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Custom String Sorting: words use only letters of `customOrder`; a proper prefix sorts first; a new list is returned.
- Temporal Key-Value Store: write timestamps never decrease; a write at the key's latest timestamp replaces it; `get` misses
  return "". Level 1 `remove(key)` erases the whole history; level 2 `remove(key, timestamp)` stores a deletion version, so
  earlier times still see old values.
- Cache with Eviction: ties on the lowest rank evict the oldest write (the preview allows any). Level 2 is a read-through,
  write-through cache over source rows given to the constructor, with `getLoadCount()`.
- Card Game III: input is the deck in deal order; output `[hand1, hand2, winner]` with 0 for a draw. Level 2 adds three-card
  poker categories (straight flush > three of a kind > straight > flush > pair > high card, ace high only). Level 3 deals
  round-robin to 2 to 17 players with the level-1 categories and returns all tied winners.
- ChatBot System: bot types "echo" (`/echo <text>`), "reverse" (`/reverse <text>`) and "count" (`/count`, user messages so
  far); log entries are `"<sender>: <text>"`; bots react in the order added and never to bot replies. Level 2 adds channels.
- Delayed Tasks Scheduler: `schedule(taskId, delayTime, currentTime)` returns the run time; `runDue(currentTime)` returns due
  ids by (run time, scheduling order); `cancel(taskId)`.
- In-Memory SQL: a value is an integer when it matches `0|-?[1-9][0-9]{0,8}`; the first stored row fixes column types and a
  disagreeing row is rejected; `select(table, conditions, orderBy, ascending)` with six comparison operators, a stable sort in
  both directions, and [] for unknown tables or columns.
- KV Store with Rollback: level 2 nested `begin`/`rollback`/`commit` (commit closes every open transaction); level 3 `count(value)`.
- Note-Taking System: caller-supplied non-decreasing times; ids `note1`, `note2`, ...; level 2 case-insensitive search ordered
  by modification time descending; level 3 tags; level 4 versions with revert as a new version.
- Persistent Key-Value Store: blob = 4-byte big-endian count, then length-prefixed ASCII key and value per entry in key order.
  Level 2 wraps it in magic bytes "PKV2" and an additive checksum and rejects malformed blobs without changing state.
- Query Pagination: one function; filters `[minTime, maxTime, minAmount, maxAmount, userId, currency]` with "" for none;
  inclusive ranges; exact cent comparison; timestamp order; 1-based pages.
- Rate Limiter: sliding window `(t - ttl, t]` counting accepted requests only; level 2 is per client.
- Recent File Tracker: file names unique; ties on date ordered by code points.
- Recipe Management System: level 2 case-insensitive exact ingredient search; level 3 ratings with exact average order; level 4
  listing by case-insensitive name prefix.
- Ring Buffer: one byte per character; the read pointer never moves on overwrite, and the unread count is capped at capacity, so
  after an overflow a read can return stale or newer bytes in cell order (this follows the preview's "independent pointers").
- Squirrel Nut Tracker: hide fills bottom-up, retrieve takes top-down, so only the total per location matters; level i holds F(i + 2).

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One post-freeze amendment changed `cases.py` after the first Python run: two hand-built
analytic-maximum expectations were wrong (the ChatBot level-1 row expected the whole 199992-entry log from
`getRecentMessages(100000)` instead of its last 100000 entries, and the In-Memory SQL row omitted the null result of the void
`createTable`). The candidates were not changed for it; the references, validators, contracts, design and specifications are
unchanged. Both previous and current hashes are recorded.

## Local checks (author self-check, not qualification)

All 7846 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 62464 seeded Python rows matched the references. The native observers pass on all 6565 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.24 s per execution under node --jitless (Delayed Tasks
Scheduler) and 0.13 s under python3 (Recent File Tracker); see `checks.json`. These runs check the code against the author's
own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and,
above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
