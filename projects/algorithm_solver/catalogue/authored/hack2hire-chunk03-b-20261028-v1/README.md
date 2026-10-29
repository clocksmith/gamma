# Hack2Hire chunk03-b: twenty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 21 of their variants, from coordinator
worklist h2h-chunk03-b (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01-a/b, chunk02-a/b/c/d, chunk03-a and later) are separate; this cohort follows the chunk01-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.
None of the 16 previews looked like a different problem from its title.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

Least certain inferences (uncertainty `high` in `contracts.json`): the output of Merge K Sorted Price Streams (one
`"t, price"` row per distinct timestamp); every Music Player method beyond the constructor, and its levels 2-3
(recent songs, removal); N-gram Split level 2 (longest-match n-grams); both Neighborhood Party levels (merged windows,
peak concurrency); both Poker levels (which patterns count as valid; level 2 as a winner search).

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. All numeric results are integers below 2**53; the modular
  count uses BigInt in JavaScript and exact floor division guards the throughput search.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (exhaustive enumeration, BFS over whole
  arrays or permutations, memoised exact search over removal orders, literal replays, quadratic scans). `cases.py` generates
  small random rows, boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 18 source-free
  tests (hand-worked examples, domain rejections, a BFS cross-check of the zero-steps recurrence, a BFS check of the rotation
  distance formula used by the analytic rows) plus the author-local candidate runner.
- Native classes (3 variants: MusicPlayer levels 1-3) follow chunk02-d: a module-global class (Python) or a property of the
  CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter.
  `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids;
  `playSong` is void and normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 105 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (21 contracts, 42 implementation artifacts, 21 `source-native` design artifacts, 21 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

Minimum Variant Conversion uses a closed form, `c + m(m-1)/2` (c ones, m the smallest positive k-window sum): clearing the
cheapest window costs m, m-1, ..., 1 and every other 1 then costs 1, and after j removals no positive window can be below
m - j, so this is also a lower bound. The reference does not use the formula; it searches every removal order and window.
Minimum Operations to Sort by Rotate and Flip runs BFS over the 2n (offset, direction) states instead of arrays.

## Freeze

References, validators, contracts, design, the case generator and `test_oracles.py` were frozen before any candidate file
existed (`pre-source-reference-freeze.json`); their hashes still match. There were no post-freeze amendments.

## Local checks (author self-check, not qualification)

All 6635 generated rows pass in both languages, through the trace adapter or `solve` and through the inferred wrapper or
direct class, with inputs unchanged. A further 98760 seeded Python rows and 19752 seeded JavaScript rows matched the
references. The native observers pass on all 912 class cases in each language with the unchanged easy16 transport. The
heaviest case takes 0.41 s per execution under node --jitless (Merge K Sorted Price Streams, 10000 streams) and 0.12 s under
python3 (Minimum Triggers, 1e5 balls); peak RSS stays below 300 MB (`checks.json`). These runs check the code against the
author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated
runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
