# Hack2Hire chunk14-a: twenty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 21 of their variants, from coordinator
worklist h2h-chunk14-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk13 and chunk14-b) are separate; this cohort follows the chunk13-b and chunk12-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names, the trade string format and the
template syntax is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Several previews stop before the rule that decides the
answer: Stock Trades Matching (the matching rule and output), Stream to Matrix Row Transformer (the fill rule and output),
Streaming Stop Token (the token-chunk rule), String Matches in Matrix (the third direction), String Reorganization (which
arrangement), Subscription Billing Statement (the output), Tail N Lines (everything except "behave like tail -n"), Text Box
Formatter (the border characters), Top K Book Sales and Top K Pins (the method names). Level 2 of Stock Trades Matching,
level 2 of Streaming Stop Token, levels 2 and 3 of Text Box Formatter and level 2 of Top 10 Words have no public text at
all; they are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Subscription
  Billing month numerators, doubled at most 6.2e7, and Top K Book Sales totals, at most 2e8); Subset Sum Target uses an exact big-integer
  bitset (Python int, JavaScript BigInt).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (prefix dynamic programming, nested list
  scans, per-cell timestamp scans, position-by-position token comparison, cell-by-cell path comparison, lexicographic
  permutation enumeration, day-by-day calendar walks with exact fractions, subset enumeration, linear membership checks,
  split-and-slice, regular-expression substitution, explicit character loops, space-by-space justification, full sorts and full
  recounts). `cases.py` generates small random rows, hand rows and analytic rows at the inferred maximum bounds.
  `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check on every
  generated row, contract layout) plus the author-local candidate runner.
- Native classes (3 variants: Top 10 Words level 2, Top K Book Sales, Top K Pins) follow requested-22-a and chunk13-b: a
  module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null (`native_protocol.py` adds the `(string|integer)[][]` return kind for the word-count pairs).
  `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 18 function variants expose
  `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 105 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (21 contracts, 42 implementation artifacts, 21 `source-native` design artifacts, 21 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Split Text into Lines: words are runs of non-space characters; the answer is the greedy line count.
- Stock Trades Matching: level 1 matches identical trade strings one-to-one; level 2 then matches leftovers on symbol, side
  and quantity (ID ignored), pairing sorted trades within a key. Both return all unmatched trades sorted by code point.
- Stream to Matrix Row Transformer: rows `[timestamp, v1, ..., vc]` per distinct timestamp (ascending), columns in code
  order; unregistered codes ignored; last arrival wins within a timestamp; values carry forward, null before the first record.
- Streaming Stop Token: output the chunks before the chunk holding the first `<END>` character, plus that chunk's prefix
  when non-empty; no token returns everything. Level 2 lets the token span chunks.
- String Matches in Matrix: the third direction is the down-right diagonal; a one-character string counts three times per cell.
- String Reorganization: the lexicographically smallest valid arrangement, or "" when none exists.
- Subscription Billing Statement: prices in cents; START and SWITCH days billed at the new plan, the END day not billed;
  billing runs to December 31; output `[["YYYY-MM", cents]]` per billed month, each month total rounded half up.
- Subset Sum Target: repeated values allowed; target 0 is reachable.
- Tag Groups Complement Finder: output sorted (the source allows any order).
- Tail N Lines: whole-text string in, string out, with `tail -n` line semantics (an unterminated last line counts).
- Template String Formatter II: branch `one` exactly for the value "1"; every `#` in the chosen branch becomes the value;
  unknown names stay unchanged; inserted values are not rescanned.
- Text Box Formatter: `+`/`-` borders and `|` sides with no inner padding, one separate box per sentence. Level 2 wraps
  greedily at maxWidth (box width = widest wrapped line); level 3 also justifies fully as in LeetCode 68 (box width = maxWidth).
- Top 10 Words: `[word, count]` lists, lowercase words. Level 2 is a `WordFrequencyTracker` with `addText` and `getTop10`;
  words never continue across calls.
- Top K Book Sales: `BookSalesTracker.recordSale(bookId, quantity)` and `getTopK(k)` returning ids, ties by ascending id.
- Top K Largest Elements: returned in non-increasing order (the source allows any order).
- Top K Pins: `PinManager.addPin(pinId, score, pinType)` with distinct integer ids and `getTopK(pinType, k)` returning ids,
  ties by smaller id.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One amendment was needed: the first candidate run exposed a bug in the frozen
Tail N Lines reference (`ref_tnl` sliced from a negative index when n exceeded the line count by less than the count, so
`["  b\n ", 3]` returned only the last line). The reference was fixed to clamp the start at 0; the inferred spec and
the candidates were not changed. The amendment records both hashes; every other frozen file is unchanged.

## Local checks (author self-check, not qualification)

All 5419 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 42872 seeded Python rows matched the references. The native observers pass on all 760 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.08 s per execution under python3 (String Matches in
Matrix) and 0.09 s under node --jitless (Stock Trades Matching level 2); see `checks.json`. Peak RSS was 175 MB for the whole
python3 `test_oracles.py` run and 118 MB for node --jitless on the heaviest single rows. These runs check the code against the
author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner
and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
