# Hack2Hire chunk05 blocked variants: nine authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers exactly the nine variants (six groups) that
[hack2hire-chunk05-v1](../hack2hire-chunk05-v1/blockers.json) left blocked because their previews stop before the
deciding rules. It does not modify chunk05-v1. Following the owner's direction of 2026-10-28, these problems are
inferred, and every inference is labelled. Problem identity is the string uid `hack2hire:<variant id>`. The layout follows
hack2hire-chunk17-b and chunk16-b.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound and example on 2026-10-29 from the preview, title, tags
and, where it recalls one, the commonly reported public version of the problem. Every contract row says
`spec_basis: inferred` and records who inferred it, which fields it used, the preview `response_sha256` and
`preview_content_sha256`, a stated uncertainty level and a `prior_blocker` block that quotes chunk05-v1's blocking reason.
Spec text is a paraphrase in the author's words. `official_interface` is null everywhere.

Uncertainty is **very high** for eight variants: their deciding rules are invented, not recovered. Count of Stable Subarrays
is **high**: its two conditions follow the commonly reported public version of that OA problem as the inferring model
recalls it, unverified against any source (bank.json also lists LeetCode 3748 as a possible title overlap; its statement
was not consulted). Design Ambient Light Sensor System's thread-safe, non-blocking contract is not modelled or tested:
every run is sequential.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Study-record identity

chunk05-v1 already holds placeholder contract records `contract:<problemId>:<variant id>:authored-v1` (statement
`missing`) for these nine variants. To avoid two records with one id, the contracts here use
`contract:<problemId>:<variant id>:authored-inferred-v1`. Approach and artifact ids follow STUDY-RECORDS.md unchanged
(chunk05-v1 has none for these variants).

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty, variant-split
  inference and `prior_blocker`. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity
  target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated, integers below 2**53 (pay in integer cents, floored
  averages computed without floating point).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (all-pairs running sums, minute-by-minute
  pay simulation, full rescans of stored readings, round replay from the deck, breaker history replay, per-word token
  comparison). `cases.py` generates hand rows, 250 small random rows and analytic rows at the inferred maximum bounds.
  `test_oracles.py` holds 10 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every
  generated row, contract layout, coverage of exactly the chunk05-v1 blockers) plus the author-local candidate runner.
- Native classes (4 variants: Design Ambient Light Sensor System, Design Card Game x2, Design Dual Circuit Breakers) follow
  chunk17-b: a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer; `test_native_observer.py/.cjs` hold source-free toy controls plus
  author-local runs. The 5 function variants expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named
  export in JavaScript).
- `study-content.json` and `study-records/`: 45 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (9 contracts, 18 implementation artifacts, 9 `source-native` design artifacts, 9 approaches), validated against
  `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Inferred rules (all inferences; see each contract row)

| Variant | Inferred rule | Algorithm |
|---|---|---|
| Count of Stable Subarrays | `countStableSegments(capacity)`: segments of length >= 3 whose equal ends each equal the sum strictly between them | prefix sums + hash map of (capacity[l], P[l+1]), O(n) |
| Dasher Payment Model 1 | `calculatePay(activities)`: [HH:MM, orderId, accepted/delivered] rows; 30 cents per minute per ongoing order | event sweep with running order count |
| Dasher Payment Model 2 | as 1, minutes in 11:00-14:00 and 17:00-20:00 pay double | sweep + closed-form weighted minutes |
| Dasher Payment Model 3 | as 2, plus `cancelled` orders earn nothing | first pass marks cancellations, then the sweep |
| Design Ambient Light Sensor System | `ALSWrapper`: `record(status, lux, timestamp)` keeps status 1 only; `getLatestLux()`; `getAverageLux(start, end)` floored, -1 when empty | sparse Fenwick trees (sum and count) over timestamps |
| Design Card Game 1 | `CardGame(deck)` with the draw order given; `playRound()` higher card wins 1 point; `getScore`, `getWinner` | draw pointer + running scores |
| Design Card Game 2 | as 1, rank = card % 13; higher rank scores both ranks + 2, equal ranks tie | same |
| Design Dual Circuit Breakers | `DualCircuitBreaker(failureThreshold, cooldown).request(t, primaryOk, secondaryOk)`: closed/open/trial breakers on primary and secondary, reroute to secondary; PRIMARY/SECONDARY/FAILED/BLOCKED | two O(1) breaker state machines |
| Detect Abusive Words | `detectAbusiveWords(words, substitutions, comment)`: indexes of whole tokens that decode, symbol by symbol, to an abusive word | trie walked with a node list (symbols branch to up to 3 letters) |

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every candidate passed every row on its first run.

## Local checks (author self-check, not qualification)

All 2298 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 36000 seeded Python rows matched the references. The native observers pass on all 1017 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.042 s per execution under python3 (Design Ambient
Light Sensor System) and 0.063 s under node --jitless (Count of Stable Subarrays, 1e5 capacities); see `checks.json`. Peak RSS
was 267 MB for the whole python3 `test_oracles.py` run and 76 MB for node --jitless on the heaviest single row. These runs
check the code against the author's own inferred contract only. Official ABI, effects, limits and correctness still need the
coordinator's isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
