# Hack2Hire chunk08-a: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk08-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk07 and chunk08-b) are separate; this cohort follows the chunk06-a and chunk07-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview describes a different problem than its title. Several stop before the part that matters most: Payment Refund
Allocation shows the row formats but not the allocation rules; Property Booking System shows the class but not its selection
rules; Priority Expiry LRU Cache shows the eviction hierarchy but no method signatures; Prefix Frequency Partition, Process
Queue and Restore String with Target Digit Sum stop before saying what to return. Random User Pairing asks for uniformly random
output, which cannot be checked exactly, so the variant-1 interface takes the random draws as an input.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest the inferred
  domains allow is a billing balance or refund amount of 10**14; the largest in the cases is a level-3 peak of 5 * 10**13).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (per-payment refund rescans, sorted-block
  comparison, full sorts of every match, linear-scan eviction, literal list and grid simulation, bitmask subset enumeration,
  slice-based pool removal, per-pair group scans, materialised ranges, per-IP timestamp scans, `str.count`, per-user rescans,
  brute-force retry of every repair, plain backtracking). `cases.py` generates small random rows, boundary rows and analytic rows
  at the inferred maximum bounds. `test_oracles.py` holds 18 source-free tests (hand-worked examples, domain rejections, a domain
  and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (5 variants: PriorityExpiryLRUCache, BookingSystem, RangeIterator, DetectionSystem, Table) follow
  requested-22-a and chunk06-a: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a
  separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised to
  null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Payment Refund Allocation: refundable balance = amount minus linked refunds; payments visited CREDIT, CREDIT_CARD, PAYPAL, then
  other types by name, newest first, then by id; returns `[paymentId, allocated]` for positive allocations; a shortfall is left
  unallocated.
- Prefix Frequency Partition returns every valid length ascending. Prefix Search I and II rank by the 0-based index of the first
  matching word, then the name in code-point order; Search II answers every prefix of a typed word with all matches.
- Priority Expiry LRU Cache: `get(key, currentTime)` returns -1 on a miss and drops an item with expiryTime <= currentTime;
  `set` on a full cache evicts exactly one item (earliest expiry among expired items, otherwise lowest priority; ties to the
  least recently accessed).
- Process Queue returns the queue size at times 0, 1, ... until empty. Property Booking picks the fewest properties, then the
  smallest total capacity, then the smallest sorted id list, and books them permanently.
- Random User Pairing: level 1 consumes the supplied draws (`r mod pool size`, swap-with-last removal) and appends the leftover
  user as a single-element list; level 2 pairs users from the two largest groups (max-heap, ties to the smaller group name).
- Range Iterator: `next` is only called while values remain. Reach End in Grid With Teleports takes teleports as
  `[r1, c1, r2, c2]` rows and returns the number of right moves, or -1 when stuck or looping.
- Realtime Bot IP Detection: `isBot(ip, t)` counts the IP's requests in `[t - W + 1, t]`, including flagged ones.
  Recipes are checked independently against the full supply.
- Reconstruct Billing Status: level 1 final balances (charges minus payments), level 2 balances as of a timestamp, level 3
  final and peak balance replayed by (timestamp, transactionId).
- Repair Bootloader Program: level 1 returns `[repeated index, accumulator]` or `[-1, accumulator]` when execution leaves the
  range; level 2 switches one jump/next so execution reaches exactly `len` and returns `[smallest such index, accumulator]`
  or `[-1, 0]`.
- Restore String returns the lexicographically smallest restoration or "". Table: `setColor` before any selection does nothing.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One post-freeze amendment: the first Python candidate run failed one analytic-maximum row
of Realtime Bot IP Detection ("every IP twice, window 1e9"). The construction built the second-half IPs from `i % 256` instead of
`(i % 50000) % 256`, so the IPs did not repeat as the stated expectation assumed. `oracles.ref_bot` (called directly; each IP
has at most two requests) agreed with the candidate on the frozen row, and both match the stated expectation on the corrected
construction. Only that construction line in `cases.py` changed; no reference, validator, contract, design or expected value
changed. The freeze file records both hashes.

After the first full run, the JavaScript Random User Pairing v2 heap was changed to build with one bottom-up heapify (as the
Python candidate's `heapq.heapify` does) and to sift with a hole, bringing its heaviest row from 0.55 s to 0.32 s under
node --jitless. The greedy algorithm and its output are unchanged.

## Local checks (author self-check, not qualification)

All 5157 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40792 seeded Python rows matched the references. The native observers pass on all 1281 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.32 s per execution under node --jitless and 0.09 s under
python3 (Random User Pairing v2, `checks.json`). These runs check the code against the author's own inferred contract only.
Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the official
specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
