# Hack2Hire chunk14-b: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk14-b (2026-10-29). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk13 and chunk14-a) are separate; this cohort follows the chunk13-b and chunk12-a layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-29 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers, operation strings and method-free field names
is copied. `official_interface` is null everywhere.

No preview clearly describes a different problem than its title. Two previews cover only part of what the title names:
Beam Search Decoding describes only greedy decoding, and Worker-Task Matching with Specialties describes only plain
least-loaded assignment without specialties. Several previews stop before the rule that decides the answer: Toy Language
Grammar (both tasks), Violation Log Analyzer (the methods), Warehouse Package Allocation (the capacity meaning and the
output), Winner in a Dot Grid Game (scoring and output), Apply Binary Array Operations (the output), Auto Email Generation
(the third input and the format) and Black Cell Covering Block List (the requested list). Level 2 of Toy Language Grammar,
level 2 of Beam Search Decoding and levels 2 and 3 of Worker-Task Matching with Specialties have no public text at all;
they are inferred extensions.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the largest are Basic
  Calculator intermediates, bounded at 1e15 by the inferred domain, and Bank Service Maximization prefix sums, below 1e14);
  JavaScript division truncates exactly with `(a - a % b) / b`.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (string comparison of substituted
  types, full log scans, substring enumeration, linear next-center scans, list-scan eviction, per-start automaton
  simulation, full board recounts, line-string building, linear worker scans, leftmost-zero scans, repeated rescans,
  per-start simulation, recursive descent with exact fractions, sorting, Cartesian products, per-block coordinate scans and
  backtracking). The Basic Calculator validator also evaluates the expression iteratively (shunting-yard) to enforce the
  grammar, no division by zero and the 1e15 bound. `cases.py` generates small random rows, hand rows and analytic rows at
  the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests (hand-worked examples, domain rejections, a
  domain and nesting check on every generated row, contract layout) plus the author-local candidate runner.
- Native classes (2 variants: Violation Log Analyzer, Weighted Cache) follow requested-22-a and chunk13-b: a module-global
  class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void methods normalised
  to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs. The 18 function variants
  expose `solve` and an inferred wrapper (`Solution.<name>` in Python, a named export in JavaScript).
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

All inferred; see each contract row for the uncertainty.

- Toy Language Grammar: types are JSON (strings for primitives and generics `T0`..`T9`, non-empty lists for tuples, depth at
  most 20). Level 1 prints a function type as `(p1, p2) -> r` with tuples as `[a, b]`. Level 2 binds generics from concrete
  argument types (a generic may bind to a tuple; repeated generics must bind identically) and returns the printed,
  substituted return type, or null on any mismatch; unbound generics stay as written.
- Violation Log Analyzer: `countPolicies(postId, start, end)`, `countPosts(policy, start, end)` and
  `countViolations(start, end)` count distinct policies, posts and (post, policy) pairs within an inclusive date range.
- Vowels Substring: counts by position, as stated.
- Warehouse Package Allocation: capacity is a per-visit burst in round-robin order starting at center 0; closing the
  current center passes the turn; the answer is the center with the most packages, the largest index on ties.
- Weighted Cache: ties among the heaviest items evict the least recently written one (the preview allows any); the item
  just written can itself be evicted; `get` returns -1 on a miss and does not change the cache.
- Wildcard Search: a substring match (the pattern need not reach the end of the string); only-star or empty patterns match at 0.
- Winner in a Dot Grid Game: the mover scores every square its stick completes, no extra turn; returns 1, 2 or 0 for a tie.
- Word Search in a Straight Line: the word lies along one of the eight directions; case-sensitive.
- Worker-Task Matching with Specialties: output is task id lists in worker input order; level 2 adds per-worker specialty
  lists, per-task types and a trailing list of unassigned task ids; level 3 adds a per-worker limit on the number of tasks.
- Apply Binary Array Operations: returns the final array.
- Auto Email Generation: the third input is `username`; the body is `Dear <username>,` then one line per category in string
  order listing keywords by first detection with their counts, or `No violations found.`; unmapped words are ignored.
- Bank Service Maximization: the balance may reach exactly 0; the answer is the largest number of customers served.
- Basic Calculator: no spaces; unary minus at the start, after `(` and after a binary operator.
- Beam Search Decoding: integer scores; level 2 returns the final beam of `beamWidth` sequences, best total first, ties by
  the lexicographically smaller index sequence (with independent steps this equals the exact top sequences).
- Black Cell Covering Block List: four lists of block top-left corners, for blocks with exactly 1, 2, 3 and 4 black cells.
- Block-Based String Assembly: bipartite matching of target positions to distinct blocks.

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One amendment was needed after the first candidate run: a hand-derived Wildcard
Search maximum row expected `n - 1` for the pattern `a*` repeated 50000 times, but that pattern needs 50000 `a` characters
in order, so the correct value is -1 (both candidates returned -1). The row now expects -1 and one added row checks pattern
`a*` against the same string. References, validators, contracts and the inferred spec are unchanged; the amendment and the
old and new `cases.py` hashes are recorded in the freeze file and `case-design-summary.json`.

## Local checks (author self-check, not qualification)

All 5159 generated rows pass in both languages, through `solve` and through the inferred wrapper or direct class, with inputs
unchanged. A further 40760 seeded Python rows matched the references. The native observers pass on all 508 class cases in
each language with the unchanged easy16 transport. The heaviest case takes 0.13 s per execution under python3 (Bank Service
Maximization) and 0.32 s under node --jitless (Apply Binary Array Operations and Worker-Task Matching level 1); see
`checks.json`. Peak RSS was 135 MB for the whole python3 `test_oracles.py` run. These runs check the code against the
author's own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated
runner and, above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
