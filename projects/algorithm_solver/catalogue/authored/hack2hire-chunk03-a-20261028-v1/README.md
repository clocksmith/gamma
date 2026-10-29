# Hack2Hire chunk03-a: seventeen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 17 of their variants, from coordinator
worklist h2h-chunk03-a (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling chunk03 cohorts
are separate; this cohort follows the chunk01-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.
All 16 previews match their titles.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

Least certain inferences (uncertainty `high` in `contracts.json`): the League Earnings match formula and rounding, the
Maximize Deployment Score scoring rule, the Maximum Stability formula, the merge rule of the Incremental String Tokenizer,
the cycle behaviour of the Interleave Iterator, duplicate handling in Largest Consecutive Skill Team, and the task of
Limit Tree Height variant 2 (minimum deletions for a height limit).

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. All numeric results are integers below 2**53. Non-integer
  values (interpolation, the league average) are exact: reduced fraction strings or integer-rounded two-decimal strings.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (literal merge scans, round-by-round
  materialisation, quadratic DPs with trial division, exhaustive 3^n assignments, subset enumeration, rebuild-and-measure
  trees, per-query rescans with Fractions). `cases.py` generates small random rows, boundary rows and analytic rows at the
  inferred maximum bounds. `test_oracles.py` holds 21 source-free tests (hand-worked examples, domain rejections, a subset vs
  threshold cross-check, a nesting-depth check) plus the author-local candidate runner.
- Native class (1 variant: InterleaveIterator) follows requested-22-a, chunk01-a and chunk02-d: a module-global class (Python) or
  a property of the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter.
  `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids and
  check per-method return kinds against the inferred interface (`next` returns `integer|null`).
  `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 85 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (17 contracts, 34 implementation artifacts, 17 `source-native` design artifacts, 17 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

N-ary trees are nested `{id, children}` objects capped at 99 node levels, so JSON nesting stays below 200. The binary tree uses a
flat LeetCode level-order list. Days for concurrent calls are UTC day numbers `floor(ms / 86400000)`; calls last at most three days.
Interpolated values are exact reduced fractions rather than floats so that both languages agree bit for bit.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). Nothing in those files changed afterwards.

## Local checks (author self-check, not qualification)

All 4376 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct class,
with inputs unchanged. A further 130110 seeded Python rows matched the references. The native observers pass on all 258
InterleaveIterator cases in each language with the unchanged easy16 transport. The heaviest case takes 0.14 s per execution
under node --jitless and 0.08 s under python3 (`checks.json`); peak RSS of the whole Python run is 211 MB. These runs check the
code against the author's own inferred contract only. Official ABI, effects, limits and correctness still need the
coordinator's isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
