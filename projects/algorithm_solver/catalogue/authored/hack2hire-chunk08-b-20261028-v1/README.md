# Hack2Hire chunk08-b: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk08-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk07 and chunk08-a) are separate; this cohort follows the chunk07-a and chunk06-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.

No preview describes a different problem than its title. Several previews stop before the part that matters most:
Shortest Hiking Distance stops before its objective, Student Reading Textbook before its day budget, Triangle Point
Membership before its output codes, User Flight Location Tracker after the record format, Tetris Block Drop after the
inputs, and Snake Game before the class methods. Subset Sum Equals K (3 variants), Template String Formatter I (2) and
Tetris Block Drop (2) have no per-variant text, so every level split is inferred.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are the
  Spam Caller Counter pair counts, at most 10^10, and triangle cross products, at most 8 * 10^14). The subset-sum bitsets
  are Python ints and JavaScript BigInts.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (binary-string rebuilding, quadratic DP,
  relaxation sweeps, list-based snake simulation, all-pairs report matching through `calendar.timegm`, set tests,
  `str.replace`, linear parameter scans, subset enumeration, per-element `startswith`, regex substitution to a fixpoint,
  row-by-row fall simulation, exhaustive 3^n colouring, whole-board line scans, area sums and in-order replay). `cases.py`
  generates small random rows, boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19
  source-free tests (hand-worked examples, domain rejections, a domain and nesting-depth check on every generated row,
  contract and class layouts) plus the author-local candidate runner.
- Native classes (2 variants: SnakeGame, TicTacToe) follow requested-22-a and chunk06-a: a module-global class (Python) or
  a property of the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace
  adapter. `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string
  uids and constructor arguments; neither class has a void method. `test_native_observer.py/.cjs` hold source-free toy
  controls plus author-local runs.
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract's `inference_uncertainty`.

- Set Parity Bits: the byte is an integer 0..255 (not an 8-character string); bit 7 becomes the parity of bits 0..6.
- Shortest Hiking Distance: minimise the longest day using at most k intermediate rests.
- Snake Game: `SnakeGame(rows, cols)`, `move("U"|"D"|"L"|"R") -> boolean`; growth on moves 5, 10, ...; the tail cell is
  vacated before the self-collision test on a non-growing move; every move after the game ends returns false.
- Spam Caller Counter: per caller, the number of matching (call, report) pairs; `[[caller, count], ...]` for positive counts,
  count descending then caller ascending.
- Spelling Bee Word Finder: dictionary order, repeats kept. String Replacement: target non-empty, leftmost non-overlapping.
- Student Reading Textbook: `minimumPagesPerDay(pages, days)`, -1 when days < n (Koko analogy).
- Subset Sum Equals K: level 1 existence, level 2 number of position-distinct subsets modulo 10^9 + 7, level 3 all distinct
  value combinations (Combination Sum II style), sorted. The preview gives k <= 10^9 with n <= 1000 and nums[i] <= 10^6; no
  pseudo-polynomial method fits one second across that whole range, so the validators add author test caps:
  min(k, sum - k) <= 10^6 (level 1), n * min(k, sum - k) <= 10^6 (level 2), and n <= 100, k <= 10^4, at most 10^4
  combinations (level 3). These caps are author choices, not preview bounds.
- Substring Wrapper: leftmost start position, then the longest element there; one wrap per word.
- Template String Formatter I: level 1 plain values; level 2 values may contain placeholders, expanded recursively (acyclic).
  The level 2 candidate caches the expansion of every key reachable from the text, so its memory is the sum of those
  expansions.
- Tetris Block Drop: the block starts fully above the grid and must land fully inside it (precondition); level 1 returns the
  grid with the block placed, level 2 also clears every full row.
- Three-Color Map Coloring: author bound of 20 nodes; adjacencies by name, no self-loops.
- Tic-Tac-Toe II: `TicTacToe(n, m, k)`, `move(row, col, player) -> player or 0` (LeetCode 348 naming); runs of k or more win.
- Triangle Point Membership: 0 degenerate, 1 only p, 2 only q, 3 both, 4 neither (closed triangle).
- User Flight Location Tracker: times `YYYY-MM-DDTHH:MM`; first departure airport before the first flight, departure airport
  at an exact departure time, `""` while airborne and for an unknown user, otherwise the last arrival airport.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). Before the freeze, five inputs were corrected after the validators rejected them
(two Tetris rows whose block could not land inside the grid, a template text and a replacement target over their length
bounds, a level-3 subset row with too many combinations) and one domain-rejection test input was replaced because it was
in fact valid. No file covered
by the freeze changed after it.

## Local checks (author self-check, not qualification)

All 5208 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with
inputs unchanged. A further 41032 seeded Python rows matched the references, and Python and node --jitless agreed on 77
large random rows at the inferred maximum sizes. Both class candidates pass the native observer on all 517 of their rows
in each language. The heaviest case takes 0.20 s per execution under node --jitless (Spam Caller Counter) and 0.18 s
under python3 (Student Reading Textbook) (`checks.json`). Peak RSS: 511 MB for the whole python3 test run including case
generation, 132 MB for node --jitless on the heaviest single rows. These runs check the code against the author's own
inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and,
above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
node test_native_observer.cjs
python3 test_study_records.py
```
