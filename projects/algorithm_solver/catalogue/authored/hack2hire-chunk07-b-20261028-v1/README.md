# Hack2Hire chunk07-b: twenty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 21 of their variants, from coordinator
worklist h2h-chunk07-b (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk06 and chunk07-a) are separate; this cohort follows the chunk06-a, chunk06-b and chunk04-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.

No preview was found to describe a different problem than its title. Two notes: the Pascal Triangle Encryption preview is a
single framing sentence with no visible rule, so its adjacent-digit-sum reduction is inferred from the title and the QUEUE tag
alone; the Minimum Menu Order Cost II preview is cut off before the conditions on the combinations it asks for.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every JavaScript Number result stays below 2**53; Minimum
  Expected Asset Cost uses Python ints and JavaScript BigInts for its exact numerators.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (exhaustive grid scans, event simulation,
  breadth-first searches, exact Fraction sums over every price, subset enumeration, per-start displacement sums, list-popping
  battle replays, descendant searches, per-window rescans, the built-in sort, frozenset conversion, joined-string line trials,
  prefix rescans, per-query root walks, literal digit-queue reductions). `cases.py` generates small random rows, boundary rows
  and analytic rows at the inferred maximum bounds (the Monster Team Battle maximum rows replay the reference, which has no
  budget). `test_oracles.py` holds 18 source-free tests (hand-worked examples, scaled copies of the analytic constructions,
  domain rejections, a nesting-depth check on every generated row) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper name), so this cohort has no
  `native_harness`, `native_protocol`, `native-bindings.json` or native observer tests.
- `study-content.json` and `study-records/`: 105 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (21 contracts, 42 implementation artifacts, 21 `source-native` design artifacts, 21 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

- Minimize a Convex Function: the black-box F is encoded as the maximum of integer lines; the answer is the leftmost minimiser
  on the grid a, a + eps, ... (within eps of a true minimiser), so outputs compare exactly. The official problem very likely
  passes a callable and accepts any point within eps.
- Minimum Expected Asset Cost: prices are modelled as discrete uniform integers a..b (the preview most likely means a
  continuous distribution) so that the optimal expectation is an exact rational; it is returned rounded half up to six decimals.
- Minimum Batteries for Call Duration: batteries are inserted in circular order, all charged at time 0; a battery ready exactly
  when needed is usable; the result counts insertions, or -1.
- Variant splits (all inferred): N-ary tree 1 = distance between two nodes, 2 = minimum distance between two node sets; Menu
  Order Cost I 1 = minimum covering cost, 2 = (cost, fewest entries); Monster Team Battle 1 = alternating attacks, 2 = defense,
  3 = speed-ordered rounds; Monsters Battle 1 = monsters that defeat every hostile (defeat is transitive down the hierarchy),
  2 = cheapest covering team with per-monster costs.
- Menu Order Cost II: all minimum-price exact covers using only entries whose items are all wanted.
- Nested Set Equality: set semantics (repeated elements ignored). Newspaper Text Alignment: the `*` border is inferred from a
  commonly reported similar assessment, not from the preview. Offset Commit: per processed offset, the new committed offset or -1.
- Minimum Swaps for Ball Grouping: no cap on the answer (a similar commonly reported assessment returns -1 above 10**9).
- Multithreaded Array Sort: the segment sort and merge run sequentially; only the sorted result is observable.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One analytic expectation was corrected before the freeze by a hand-worked scaled test: the
alternating a/b chain row for Palindromic Storage Paths had assumed every segment is palindrome-able, but an even-length segment
qualifies only when its length is a multiple of 4. No post-freeze amendments.

## Local checks (author self-check, not qualification)

All 5425 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A further
42888 seeded Python rows matched the references. The heaviest case takes 0.22 s per execution under node --jitless (Monster Team
Battle level 3, 100 against 100 monsters) and 0.21 s under python3 (Palindromic Storage Paths, 100000-node chain)
(`checks.json`). These runs check the code against the author's own inferred contract only. Official ABI, effects, limits and
correctness still need the coordinator's isolated runner and, above all, the official specifications. Qualification status is
unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
