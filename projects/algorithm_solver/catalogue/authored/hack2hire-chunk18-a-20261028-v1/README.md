# Hack2Hire chunk18-a: thirteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 10 Hack2Hire coding groups and all 13 of their variants, from coordinator
worklist h2h-chunk18-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk17 and chunk18-b) are separate; this cohort follows the chunk17-b and chunk16-b layout, without the native-class
files because no variant here is a class (as in chunk16-a).

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, parameter names and command names is copied.
`official_interface` is null everywhere, and every function name is invented.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Highest Scoring Movie Group (the scoring rule and the output), Highway Checkpoint (everything after the fee example),
Matrix Transformation with Commands (the command list is cut off after two commands), Maximum Number of Balanced Shipments
(the conditions of the split) and Maximum Grid Jumping Path (the objective and the output). Maximum Grid Jumping Path has four
variant ids and no per-variant text, so variants 2 to 4 are guessed follow-ups. Maximize Task Scheduling Within Time Limit is
modelled by a greedy rule (see below), which is not a true maximum in every packing case.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are the
  1e14-scale sums of Make Array Bitonic, Make Power Non-decreasing and Highest Scoring Movie Group and the 1e15-scale toll
  totals of Highway Checkpoint); path counts are reduced modulo 1000000007 after every addition.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (per-group sorting, per-plate log
  rescans, per-peak height trials, exhaustive enumeration of target arrays, direct command application, exhaustive sign
  assignment, linear slot scans, exhaustive path enumeration, a quadratic partition dynamic programme and all-pairs
  reachability). `cases.py` generates hand rows, 250 small random rows and analytic rows at the inferred maximum bounds per
  variant. `test_oracles.py` holds 13 source-free tests (hand-worked examples, domain rejections, a domain and nesting check
  on every generated row, contract layout) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper, `Solution.<name>` in
  Python and a named export in JavaScript), so this cohort has no `native_harness`, `native_protocol`, `native-bindings.json`
  or native observer tests.
- `study-content.json` and `study-records/`: 65 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (13 contracts, 26 implementation artifacts, 13 `source-native` design artifacts, 13 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Highest Scoring Movie Group: a group scores the sum of its k highest integer similarity scores (all of them when smaller);
  the answer is the best group index, the smallest on ties.
- Highway Checkpoint: records are `[plate, checkpoint]` in pass order; each vehicle pays 10 times the position difference for
  every two consecutive passes; the output is `[plate, total]` for every plate, sorted by plate, including totals of 0.
- Make Array Bitonic: the non-zero block is exactly 1, 2, ..., k, ..., 2, 1 (steps of 1) and must be non-empty; the input has
  at least one positive element.
- Make Power Non-decreasing: the answer is the sum of adjacent drops.
- Matrix Transformation with Commands: only `reverseRow r` and `swap r1 r2` are modelled; the returned value is the final matrix.
- Maximize Negative Signs: prefix sums must be strictly positive; the answer is the count of minus signs.
- Maximize Task Scheduling Within Time Limit: n * m slots that each run one task at a time; tasks start shortest first on the
  earliest-free slot and count when they end at or before minute 60. The hand example `[20, 20, 20, 30, 30]` on two slots gives
  4 under this rule, although a perfect packing fits 5.
- Maximum Grid Jumping Path: the path ends on first entering the bottom row and scores the sum of the visited cells. Variant 1
  has no special jump; variant 2 allows at most k jumps; variant 3 returns the lexicographically smallest maximum-score cell
  list; variant 4 counts maximum-score paths modulo 1000000007.
- Maximum Number of Balanced Shipments: every parcel must be shipped; 0 when no split works.
- Minimum Vertices to Traverse Directed Graph: cycles, self-loops and repeated edges are allowed; the answer is the number of
  source strongly connected components.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: the first candidate run passed every row.

## Local checks (author self-check, not qualification)

All 3366 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A
further 26472 seeded Python rows matched the references. The heaviest case takes 0.22 s per execution under node --jitless
(Highest Scoring Movie Group) and 0.08 s under python3 (Maximum Grid Jumping Path variant 4); see `checks.json`. Peak RSS was
335 MB for the whole python3 test run and 120 MB for node --jitless on the heaviest single rows. These runs check the code
against the author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's
isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
