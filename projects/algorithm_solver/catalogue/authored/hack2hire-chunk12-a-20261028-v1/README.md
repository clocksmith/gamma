# Hack2Hire chunk12-a: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk12-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk11 and chunk12-b) are separate; this cohort follows the chunk10-a and chunk11-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and cell symbols is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Longest Valid Parentheses is not LeetCode 32: its preview
introduces three bracket kinds with nesting rules and stops before stating the rules. Several other previews stop before the
rule that decides the answer: Linked User Records by Similarity (the task itself), Load Factor Calculation (input and output
formats), Matrix Escape (the task and timing), Max Consecutive ON Servers (the objective), Maximum Balanced Task Assignment (the
objective), Maximum Building Height (the output), Maximum Vacation With Minimum Flights (the objective) and MinMax Queue (the
min and max method names). Levels 2 and 3 of Linked User Records have no public text at all; they are inferred extensions.
The Matrix Escape group title in the cached preview has a trailing space; contracts use the trimmed title.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Load
  Factor path counts, capped at 2**53 - 1 by the domain, and Maximum Multiplier Path products up to 10**11). Linked User
  Records weights and thresholds are converted to exact integer ten-thousandths, never added as binary floats.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (parent-chain walks, pairwise Fraction
  scores, label propagation, fixed-point relaxation, interval recursion, minute-by-minute simulation, all-window scans,
  exhaustive fly/rest masks, direct replays, augmenting-path flow, per-cell searches, point counting, simple-path enumeration,
  quadratic DP, nested recursive merges and plain list scans). `cases.py` generates small random rows, hand rows and analytic
  rows at the inferred maximum bounds. `test_oracles.py` holds 20 source-free tests (hand-worked examples, a check of the
  Max Consecutive ON window rule against a search over real range flips, domain rejections, a domain and nesting check on
  every generated row, contract layout) plus the author-local candidate runner.
- Native class (1 variant: MinMax Queue) follows requested-22-a, chunk10-a and chunk11-b: a module-global class (Python) or a
  property of the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter.
  `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids
  and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
  The 17 function variants expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- N-ary trees (Level With Maximum Nodes, Merge N-ary Tree, Min Root-to-Leaf Path Sum) travel as canonical LeetCode N-ary
  level-order lists (root, null, then each node's child group closed by null), so arguments stay flat whatever the tree height.
  The merged tree is returned in the same form; an empty tree is `[]` (level 0, path sum 0).
- Linked User Records: similarity is the sum of the weights of fields on which both records hold the same non-empty value;
  records link when similarity >= threshold. Level 1 lists linked pairs, level 2 transitive groups of two or more, level 3
  each record's best linked match (earliest row on ties, "" when none).
- Load Factor Calculation: every service passes its full load to each callee, so load = number of paths from the entry;
  the output lists every named service sorted by name, unreachable ones with 0.
- Longest Valid Parentheses: ranks () < [] < {}; a pair may contain pairs of the same or lower rank; return the longest
  valid substring length.
- Matrix Escape: reach any border cell; the threat spreads one cell per minute through non-wall cells and catches you on a
  tie; return minutes or -1.
- Max Consecutive ON Servers: states as a 0/1 string; answer = longest window with at most k blocks of zeros.
- Max Fly Distance: flying needs at least 1 energy; bound n * k <= 1e6 for the DP.
- Max Levels from Each Index: non-negative layers and energy; one score per start index.
- Maximum Balanced Task Assignment: returns the total m * t.
- Maximum Building Height: X blocks moves; 0 with no building tile, -1 when a building tile cannot reach parking.
- Maximum Multiplier Path: integer multipliers 0..10 and n <= 12 for exact products (the original likely uses real
  numbers); 1 when start == end, -1 when unreachable.
- Maximum Vacation With Minimum Flights: `days[city][week]` as in LeetCode 568; returns [max days, min flights].
- MinMax Queue: `getMin` and `getMax`; dequeue/getMin/getMax only on a non-empty queue.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every frozen file is unchanged.

## Local checks (author self-check, not qualification)

All 4666 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 27000 seeded Python rows matched the references. The native observers pass on all 255 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.11 s per execution under node --jitless (Load Factor
Calculation) and 0.15 s under python3 (Matrix Escape); see `checks.json`. Peak RSS of the whole python3 test run was 311 MB.
These runs check the code against the author's own inferred contract only. Official ABI, effects, limits and correctness still
need the coordinator's isolated runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
