# Hack2Hire chunk12-b: seventeen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 17 of their variants, from coordinator
worklist h2h-chunk12-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk11 and chunk12-a) are separate; this cohort follows the chunk10-a and chunk11-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers and method or parameter names is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Minimize Cost with Vouchers (the objective and the rounding of a halved price), Minimize Shopping Department Visits
(the output), Minimum Coin Combination Counts (the output), Minimum Flips for Grid Symmetry (the output), Minimum Idleness
After K Flips (the flip rule and the output), Minimum Machines for Task Scheduling (the interval format and the output),
Minimum Root-to-Leaf Path Sum (the output format), Minimum Starting Battery Level (every rule after "strictly above 0" and the
output), Minimum Distance to All Points (the tie rule) and Nested String with Brackets Parsing (at least one further
well-formedness condition and the output). Level 2 of Nested String with Brackets Parsing has no public text at all; it is an
inferred extension.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are the
  1e14-scale totals of Minimum Starting Battery Level, Minimize Cost with Vouchers and Minimum Distance to All Points).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (all-pairs scans, a linear search over x,
  a sorted list of all halving savings, linear product lookups, count-vector enumeration, all-candidates distance sums,
  union-find over mirrored cells, flip-subset enumeration, per-start overlap counts, recursive path enumeration, step-by-step
  battery simulation, per-start sets, bitmask breadth-first search, day-by-day leaf removal, repeated "()" deletion,
  recursive descent and integer increments). `cases.py` generates hand rows, 250 small random rows and analytic rows at the
  inferred maximum bounds per variant. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections,
  a domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper, `Solution.<name>` in
  Python and a named export in JavaScript), so this cohort has no `native_harness`, `native_protocol`, `native-bindings.json`
  or native observer tests.
- `study-content.json` and `study-records/`: 85 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (17 contracts, 34 implementation artifacts, 17 `source-native` design artifacts, 17 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Minimal Difference in Two Arrays: non-empty sorted lists with duplicates allowed; ties by smallest a, then smallest b (from the preview).
- Minimal Video Score Reduction: impossible (-1) exactly when there are more positive scores than k; 1 when nothing is positive.
- Minimize Cost with Vouchers: a voucher replaces p by floor(p / 2); vouchers need not all be used; return the minimum total.
- Minimize Shopping Department Visits: return the number of distinct departments of the listed products; unknown products are
  ignored. The original may instead ask for visits saved against walking the list in order.
- Minimum Coin Combination Counts: return per-denomination counts (aligned with `coins`) of a fewest-coins combination, preferring
  more coins of larger denominations on ties; [] when the target cannot be made. This is the least certain reading here.
- Minimum Distance to All Points: x must be an input value; the smallest optimal x wins ties.
- Minimum Flips for Grid Symmetry: the grid is a list of "B"/"W" strings; return the minimum flip count.
- Minimum Idleness After K Flips: at most k single-character flips; minimise the longest run.
- Minimum Machines for Task Scheduling: half-open [start, end) intervals, 0 for no tasks.
- Minimum Root-to-Leaf Path Sum: LeetCode level-order input; return the values of the minimum-sum path, leftmost on ties, [] for an empty tree.
- Minimum Starting Battery Level: usage may be negative (recharge); return max(1, largest prefix sum + 1).
- Minimum Subarray with K Unique Integers and Minimum Swaps to Group Evens First: as in the previews; negative values use the
  mathematical parity.
- N-ary Tree Leaf Node Removal: LeetCode N-ary level-order input; each day is returned sorted ascending to fix the free order.
- Nested String with Brackets Parsing: level 1 checks only the parenthesis rules (letters and commas unrestricted); level 2 parses
  one well-formed nested comma list, depth at most 100, into nested arrays of strings.
- Next Greater Palindrome: strictly greater, decimal strings up to 1e5 digits without leading zeros.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every frozen file is unchanged.

## Local checks (author self-check, not qualification)

All 4413 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A
further 34768 seeded Python rows matched the references. The heaviest case takes 0.16 s per execution under node --jitless and
python3 (Minimal Video Score Reduction); see `checks.json`. Peak RSS was 205 MB for the whole python3 test run and 110 MB for
node --jitless on the heaviest single rows. These runs check the code against the author's own inferred contract only.
Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the official
specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
