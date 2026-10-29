# Hack2Hire chunk09-b: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk09-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk08 and chunk09-a) are separate; this cohort follows the chunk08-a and chunk07-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and row formats is copied.
`official_interface` is null everywhere.

No preview describes a different problem than its title ("Singler" in Count Singler Role Co-occurrences is the source's
spelling; the preview is about singers). Several previews stop before the part that matters most: Calculate Board Score shows
only the tile encoding, not the scoring rule; Chunk a List of Lists shows only the continuous-stream reading, not the chunking
rule; Company Role Assignment shows only the first validation rule; Count Dropped Requests does not state its three limits;
Counting Words in a Text stops before its grouping rules; Count Maximum Borrowing Days and Count Incorrect Sale Prices do not
show their return value. Credit Card Fraud Detection has three variants, but the preview describes only part 1 (approve
everything); parts 2 and 3 are the author's guess at a progression. Count Objects in Pin relies on a black-box comparison,
modelled here as a grid of object ids.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest result in the
  cases is a board score of 9 * 10**10). Count Incorrect Sale Prices compares JSON numbers by exact numeric equality.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (label propagation for grid regions and
  objects, quadratic rescans, per-interval rescans, materialised flattening, list scans of current associations, recursive
  child expansion, point-level BFS, per-window recounts, permutation search, all-pairs performance comparison, repeated
  minimum selection). `cases.py` generates small random rows, boundary rows and analytic rows at the inferred maximum bounds.
  `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every
  generated row, contract layout) plus the author-local candidate runner.
- Native class (1 variant: PointMatrix) follows requested-22-a and chunk08-a: a module-global class (Python) or a property of
  the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter.
  `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids,
  constructor arguments and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls
  plus author-local runs.
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Calculate Board Score: sum over 4-connected same-terrain regions of tiles x crowns. Process Starvation returns every
  process's time (0 when not starved).
- Candlesticks are `[start, max, min, open, close]` for non-empty 10-unit intervals, ordered by start; times are distinct.
- Chunk a List of Lists re-chunks the stream into chunks of `size` values with a shorter last chunk.
- Company Role Assignment: `ALREADY_EXISTS`, then `ROLE_TAKEN` (another contact holds that role at that company), else `VALID`,
  and valid associations join the set for later items.
- Compress N-ary Tree takes and returns preorder rows `[value, childValues]`; promoted children take the compressed node's place.
- PointMatrix: `addPoint` is idempotent; queries on unplaced points return false / -1; `getMinSteps` of a point to itself is 0.
  The testing bound caps the total work of `getMinSteps` calls (sum of placed points at each call) at 2e6.
- Count Alert Triggers counts sliding windows with `bad * 100 >= percent * duration` and bad meaning `errors > threshold`.
- Count Dropped Requests uses the 3 per second, 20 per 10 seconds and 60 per minute limits of the widely known
  throttling-gateway exercise; the preview does not state them.
- Count Maximum Borrowing Days returns the longest valid plan. The author could not derive the greedy rule the GREEDY tag
  suggests (smallest-payback-first is wrong; `test_oracles.py` has a counterexample), so n is bounded at 16 and the candidates
  use an exact subset DP; the reference is a permutation search.
- Count Objects in Pin counts groups of 4-adjacent object pixels the black box links (same id).
- Role co-occurrence counts each singer once per role pair; rows are ordered by role, then other role.
- Counting Words returns `[word, frequency]` for the k highest distinct frequencies, by frequency descending, then word.
- Credit Card Fraud Detection returns `[unique_id, decision]` in timestamp order (ties keep input order). Part 2 adds
  `card_number`, `merchant` and `max_amount` rules; part 3 adds fraud reports that block the reported card for requests with a
  strictly later timestamp.

## Freeze and amendment

References, validators, contracts, design, the case generator and `test_oracles.py` were frozen before any candidate file
existed (`pre-source-reference-freeze.json`). There were no amendments after the freeze.

## Local checks (author self-check, not qualification)

All 4635 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 36672 seeded Python rows matched the references. The native observers pass on all 254 PointMatrix cases
in each language with the unchanged easy16 transport. The heaviest case takes 0.39 s per execution under node --jitless and
0.31 s under python3 (PointMatrix, `checks.json`). These runs check the code against the author's own inferred contract only.
Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the official
specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
