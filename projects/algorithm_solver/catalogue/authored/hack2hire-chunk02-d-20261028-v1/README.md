# Hack2Hire chunk02-d: thirty-three authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 18 Hack2Hire coding groups and all 33 of their variants, from coordinator
worklist h2h-chunk02-d (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01-a/b, chunk02-a/b/c) are separate; this cohort follows the chunk01-a adaptations.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. All numeric results are integers below 2**53. Money is handled
  in integer cents or hundredths of a share, never floats.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (literal replays, snapshots, exhaustive
  enumeration, quadratic scans, reverse search). `cases.py` generates small random rows, boundary rows and analytic rows at the
  inferred maximum bounds. `test_oracles.py` holds 23 source-free tests (hand-worked examples, domain rejections, a forward-vs-reverse
  tile search cross-check, a diff reconstruction property) plus the author-local candidate runner.
- Native classes (11 variants: ModSystem x3, RectangleBoard x4, Spreadsheet x2, WorkQueue x2) follow requested-22-a and chunk01-a:
  a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json`
  adapt the direct-class observer to string uids, constructor arguments and void methods normalised to null. Return kinds are
  checked against the inferred interface. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 165 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (33 contracts, 66 implementation artifacts, 33 `source-native` design artifacts, 33 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

The work queue is a deterministic logical-time call sequence: every method takes the current time, and lease expiry is
processed before each call. Concurrency is not modelled beyond that. The rate limiter, profiler and hotel scheduler take
their event streams as injected arrays. The spreadsheet uses integers instead of the source's doubles so that both languages
are exact (stated in its spec).

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed. Post-freeze
changes, all recorded in `pre-source-reference-freeze.json` and `case-design-summary.json`, were:

1. Nested-tree depth cap lowered from 5000 to 200, with the permission maximum row's chain shortened to match. Depth 5000
   overflowed Python recursion in `copy.deepcopy` and in the easy16 recursive encoder.
2. The spreadsheet maximum row shrunk from a 1000-cell chain to 600 cells, to fit the per-case CPU budget.
3. `contracts.json` rows reshaped to the chunk01-a schema. Spec text and interfaces did not change.

No reference or expected-value rule changed. The RectangleBoard candidates were restructured to flat per-id arrays for speed
under `node --jitless`.

## Local checks (author self-check, not qualification)

All 8115 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct class,
with inputs unchanged. A further 40375 seeded Python rows matched the references. The native observers pass on all 2632 class
cases in each language with the unchanged easy16 transport. The heaviest case takes 0.17 s per execution under
node --jitless and 0.16 s under python3 (`checks.json`). These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all,
the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
