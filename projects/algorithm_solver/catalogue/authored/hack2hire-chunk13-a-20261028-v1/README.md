# Hack2Hire chunk13-a: eighteen authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 18 of their variants, from coordinator
worklist h2h-chunk13-a (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk12 and chunk13-b) are separate; this cohort follows the chunk12-a and chunk11-b layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, method names and card symbols is copied.
`official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Optimal Stock Price Subsequence names LeetCode 2926 as its
base but states the balance condition as price plus index (LeetCode uses price minus index); the contract follows the preview.
Several previews stop before the rule that decides the answer: Non-connected People Pairs (the task), Optimal Stock Price
Subsequence (the objective), Optimal Team Selection (the objective), Organize Books to Shelves (the output), Persistent Stack
(every operation after the constructor), Racing Points and Winner (everything after the scoring rule), Rank Songs by
Popularity (the ranking rule), Rank Vehicles by Contribution (the ranking rule), Rearrange Houses in Neighborhoods (the output)
and Reduce The Maximum To Even K Times (the rest of the operation, the role of `m` and the output). Variant 2 of Pin Board
Connectivity and of Racing Points and Winner has no public text at all; both are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are the
  Non-connected People Pairs count, about 5e9, and the Optimal Stock Price sums and Reduce The Maximum sums, at most 1e14).
  The JavaScript Rearrange Houses heap packs (copies, number) into one exact integer key below 2**48.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (label propagation, plain-set replays,
  log rescans, exhaustive subset searches, linear scans, full list copies per version, fixed-point relaxations, set comparison
  with every straight, parent-chain walks with list rescans, per-rider and per-vehicle rescans, selection by recounting,
  backtracking feasibility plus full re-sorting, and repeated linear maximum scans). `cases.py` generates small random rows,
  hand rows, every five-card hand, and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 20 source-free
  tests (hand-worked examples, a 3000-input check that the canonical Rearrange Houses filling succeeds exactly when
  backtracking finds an arrangement, domain rejections, a domain and nesting check on every generated row, contract layout)
  plus the author-local candidate runner.
- Native classes (2 variants: Oldest One-Time Visitor as `VisitorTracker`, Persistent Stack as `PStack`) follow
  requested-22-a, chunk11-b and chunk12-a: a module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 16 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 90 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (18 contracts, 36 implementation artifacts, 18 `source-native` design artifacts, 18 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Non-connected People Pairs: count unordered pairs in different friend groups.
- Obstacle Placement and Block Check: the result is one string of "1"/"0" characters; repeated placements change nothing;
  checks satisfy 1 <= size <= x so the range never goes below 0.
- Oldest One-Time Visitor: `login(username)` and `getOldestOneTimeVisitor()`, returning "" when nobody qualifies.
- Optimal Stock Price Subsequence: maximum sum of a non-empty balanced subsequence; negative prices allowed for generality.
- Optimal Team Selection: returns the largest valid team size.
- Organize Books to Shelves: returns the shelf chosen for each book.
- Palindrome Check with Ignore Set: case-sensitive one-character strings; an empty filtered sequence is a palindrome.
- Persistent Stack: versions are integer handles (0 = empty, the k-th push returns k); `push(version, val)`, `pop(version)`
  (returns the version pushed onto), `peek(version)`, `size(version)`. The handle design keeps the trace plain JSON.
- Pin Board Connectivity: pin1 != pin2; a pin on no board is related to nothing. Variant 2 returns the fewest boards on a
  route (1 when one board holds both), -1 when unrelated.
- Poker Straight Sequence Check: five distinct values; no wrap-around straight.
- Print Employee Org Chart: depth-first from the CEO, siblings in input order, four dashes per level, no trailing newline;
  output at most 4e6 characters.
- Racing Points and Winner: variant 1 returns the winner (ties to the smallest name); variant 2 returns the full standings
  ordered by points, then 1st, 2nd and 3rd place counts, then name.
- Rank Songs by Popularity: LeetCode 1366 style positional votes, final ties to the smaller id.
- Rank Vehicles by Contribution: contribution = chunk ids sent (repeats counted); every vehicle seen is ranked; ties by id.
- Rearrange Houses in Neighborhoods: a canonical filling (neighborhoods in input order, most remaining copies first, smaller
  number on ties) so the answer is exact; [] when impossible. The original likely accepts any valid arrangement.
- Reduce The Maximum To Even K Times: each operation replaces the maximum N with (N - N mod 2) / 2; the result is the final
  sum modulo m.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). No amendment was needed: every frozen file is unchanged. After the freeze, the
JavaScript Rearrange Houses heap was rewritten (same algorithm, numeric keys) because the first version took 1.77 s on the
largest row under node --jitless.

## Local checks (author self-check, not qualification)

All 5710 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 45056 seeded Python rows matched the references. The native observers pass on all 514 class cases in each
language with the unchanged easy16 transport. The heaviest case takes 0.39 s per execution under node --jitless (Rearrange
Houses in Neighborhoods) and 0.19 s under python3 (the same variant); see `checks.json`. Peak RSS of the whole python3 test run
was 400 MB. These runs check the code against the author's own inferred contract only. Official ABI, effects, limits and
correctness still need the coordinator's isolated runner and, above all, the official specifications. Qualification status is
unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
