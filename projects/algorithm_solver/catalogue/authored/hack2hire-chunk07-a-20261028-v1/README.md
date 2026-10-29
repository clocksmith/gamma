# Hack2Hire chunk07-a: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk07-a (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk06 and chunk07-b) are separate; this cohort follows the chunk06-b and chunk04-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers and the trade record format is copied.
`official_interface` is null everywhere.

No preview describes a different problem than its title. Three previews stop before the part that matters most: Maximum
Combination Health shows only its story (servers, health, model series, a diversity limit), Maximum Testing Efficiency stops
before the efficiency formula, and Maximum Task Rewards stops before its objective and output. Margin Call's preview covers
only the level-1 portfolio replay.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest is the level-1
  Margin Call cash, at least -10^10; Maximize Portfolio Floor Value stops summing as soon as the budget is exceeded).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (substring enumeration with greedy
  subsequence tests, sort-and-scan after every insertion, all-substring checks, quadratic prefix scans, share-by-share margin
  liquidation over a list ledger, border filtering of whole squares, subset enumeration, unit-step budget search, all-pairs XOR,
  explicit right/down path enumeration). `cases.py` generates small random rows, boundary rows and analytic rows at the
  inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain
  check on every generated row, contract layout) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper name), so this cohort has no
  `native_harness`, `native_protocol`, `native-bindings.json` or native observer tests.
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

- Margin Call: three variants inferred as cumulative levels. Level 1 replays trades from cash 1000 and returns
  `[["CASH", cash], [symbol, shares], ...]` as decimal strings, symbols ascending; a sell larger than the holding is clamped
  (inferred). Level 2: when cash is negative after a trade, sell one share at a time of the held symbol with the highest latest
  price (ties: smallest symbol). Level 3: `<stock>O` is an option on `<stock>`; during a margin call stock shares are locked up
  to the option count, options are always sellable, and freed shares are sellable at once. The candidates sell in closed form
  (including option/stock alternation); the reference sells share by share.
- Longest Consecutive Segment After Insertions: a query on an occupied point, or on a point whose two neighbours are both
  occupied, builds nothing; an answer is still recorded. Under this rule runs can never merge.
- Max Matrix Border Distinct Sum: score = sum of distinct frame values; Max Non-overlapping Tasks: touching endpoints do not
  overlap; Maximize Portfolio Floor Value: one upgrade raises a value by 1; Maximum Combination Health: at most k distinct
  series, positive health; Maximum Distinct Split Sum: distinct(prefix) + distinct(suffix); Maximum Task Rewards: total profit;
  Maximum Testing Efficiency: executed tests minus (t2 - t1); Maximum Value of Valid Expression Path: left-to-right evaluation;
  Minimal Board Length for Holes: L is at least 1.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). Five hand-worked expectations in `test_oracles.py` were corrected before the freeze, after
the references disagreed with them; each was rechecked by hand and the reference was right. One post-freeze amendment: the first
candidate run showed that the frozen analytic expectation for the Longest Consecutive Segment row "even points, then odd points"
was wrong (the last odd point has an empty right neighbour, so the final answer is 2, not 1). Both languages agreed with each
other, and the reference gives the corrected value on the same construction at n = 10, 100 and 400. Only that expected value in
`cases.py` changed; no reference, validator, contract or design changed. The freeze file records both hashes.

## Local checks (author self-check, not qualification)

All 4665 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A further
36832 seeded Python rows matched the references, and Python and node --jitless agreed on 73 large random rows at the inferred
maximum sizes. The heaviest case takes 0.09 s per execution under node --jitless and 0.08 s under python3 (Maximize Portfolio
Floor Value, `checks.json`). These runs check the code against the author's own inferred contract only. Official ABI, effects,
limits and correctness still need the coordinator's isolated runner and, above all, the official specifications.
Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
