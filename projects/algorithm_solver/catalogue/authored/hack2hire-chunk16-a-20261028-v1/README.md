# Hack2Hire chunk16-a: seventeen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 17 of their variants, from coordinator
worklist h2h-chunk16-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk15 and chunk16-b) are separate; this cohort follows the chunk15-b and chunk14-b layout, without the native-class
files because no variant here is a class (as in chunk12-b).

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers and parameter names is copied.
`official_interface` is null everywhere, and every function name is invented.

No preview clearly describes a different problem than its title. The previews for Maximize Number With K Swaps and Maximize
Edge Sum in Graph do match their titles, though "swaps" in the first title actually means replacing digits with 5. Several
previews stop before the rule that decides the answer: Group Elements by Shared Properties (the output), Highest Earning
Experience Tracker (the tie rule, the empty answer and the output form), Level Order Task Scheduling (the output and the cycle
case), Maximum Ski Score (how the lodge and the finish lines are identified, and the score formula), Maximum Sprint Points Sum
(the window rule and the inputs) and Merge JSON Event Logs (the requested output). Variant 2 of Grep With Context Lines has no
public text at all, so it is a guessed follow-up.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are the
  1e14-scale totals of Highest Earning Experience Tracker and Maximum Profit Query Selection and the 5e14-scale point sums of
  Maximum Sprint Points Sum). Jaccard Business Similarity returns a float computed as integer hundredths divided by 100 once,
  so both languages return the same double.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (per-line window scans, all-pairs
  breadth-first search, full rescans of a totals map, exact fractions, repeated rescans of remaining tasks, direct
  prefix/suffix comparison, all label permutations, all change subsets, all triple partitions, repeated subtraction,
  depth-first path enumeration, day-by-day expansion, direct overlap comparison, sorting of all events, half-unit grid painting
  and set sorting). `cases.py` generates hand rows, 250 small random rows and analytic rows at the inferred maximum bounds per
  variant. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a domain and nesting check
  on every generated row, contract layout) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper, `Solution.<name>` in
  Python and a named export in JavaScript), so this cohort has no `native_harness`, `native_protocol`, `native-bindings.json`
  or native observer tests.
- `study-content.json` and `study-records/`: 85 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (17 contracts, 34 implementation artifacts, 17 `source-native` design artifacts, 17 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Grep With Context Lines: variant 1 returns the included line strings in order, once per position. Variant 2 (a guess, nothing
  public) takes separate `before`/`after` counts and returns blocks of consecutive included lines, like `grep -B/-A` groups.
- Group Elements by Shared Properties: elements are `[id, p1, p2, p3]`. Elements are linked by an equal value in the same
  position, and links are transitive. The output is groups of ascending ids, ordered by smallest id, including singletons.
- Highest Earning Experience Tracker: returns one answer per "Q". Ties go to the smallest name, "" comes back before any update,
  and deltas may be negative.
- Jaccard Business Similarity: exact halves round up (1/8 gives 0.13). An empty string has no words.
- Level Order Task Scheduling: inputs are `tasks` and `dependencies`. The output is Kahn levels, each sorted; a cycle gives [].
- Longest Prefix And Suffix: the longest proper border; overlap is allowed.
- Maximize Edge Sum in Graph: nodes are 0-based and the graph is simple. The answer is the sum of label times degree, with
  sorted degrees.
- Maximize Number With K Swaps: at most k replacements (not exactly k), returned as a string.
- Maximize Server Throughput: exactly floor(N / 3) clusters.
- Maximum Profit Query Selection: inputs are two parallel lists plus k.
- Maximum Ski Score: start at the checkpoint named "lodge" and end at any checkpoint with no outgoing route. The score is the
  rewards of the checkpoints arrived at minus the route costs. This is the least certain reading here.
- Maximum Sprint Points Sum: the best k consecutive days on the cyclic schedule, with 1 <= k <= total days.
- Merge Common Substring: the overlap may be the whole shorter string.
- Merge JSON Event Logs: all events are merged by (time, serverId, position), and each output event gets a `serverId` field.
- Merge Two Interval Lists: closed intervals; touching intervals are merged.
- Merge Unique Arrays: returns a new array.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One amendment was needed after the first candidate run. The Jaccard Business Similarity
analytic maximum row used 3-letter word codes for indices up to 37500. Those codes repeat after 26**3 = 17576, so both strings
held the same 17576 distinct words: the true answer is 1.0, and both candidates returned 1.0, but the row expected 0.33. The
row now uses 4-letter codes for two 20000-word strings that share 10000 words (expected 0.33). References, validators,
contracts and the inferred spec are unchanged. The amendment and the old and new `cases.py` hashes are recorded in the freeze
file and in `case-design-summary.json`.

## Local checks (author self-check, not qualification)

All 4414 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A
further 34848 seeded Python rows matched the references. The heaviest case takes 0.26 s per execution under node --jitless
(Maximum Ski Score) and 0.09 s under python3 (Maximum Ski Score); see `checks.json`. Peak RSS was 428 MB for the whole python3
test run and 166 MB for node --jitless on the heaviest single rows. These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all, the
official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
