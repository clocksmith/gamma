# Hack2Hire chunk06-a: twenty-one authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 21 of their variants, from coordinator
worklist h2h-chunk06-a (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk05 and the other chunk06 cohorts) are separate; this cohort follows the chunk04-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.

No preview describes a different problem than its title. Two notes: the "Find Defendency Bottleneck" title is spelled that
way at the source while its preview describes build dependencies; the "Find Special Sequence Pairs" preview is only a story
(ancient DNA, a genome-matching tool) with no visible rule, so its reverse-complement pair rule is inferred from the title and
theme alone.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Integer results stay below 2**53. The bitsets of the
  multi-path middle-course variant are Python ints and JavaScript BigInts.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (per-party rescans, innermost-call regex
  rewriting, exhaustive enumeration of factory options, a literal emulation of the preview's FileSystem API, repeated relaxation
  sweeps for grid and DAG distances, explicit path enumeration, all-pairs comparison), plus two maze closed forms. `cases.py`
  generates small random rows, boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 20
  source-free tests (hand-worked examples, domain rejections, closed-form-vs-relaxation checks, a nesting-depth check on every
  generated row) plus the author-local candidate runner.
- Native class (1 variant: FileSystemStats) follows requested-22-a, chunk02-d and chunk04-a: a module-global class (Python) or
  a property of the CommonJS `solve` export (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace
  adapter. `native_harness.py/.cjs`, `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string
  uids, constructor arguments and void methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls
  plus author-local runs.
- `study-content.json` and `study-records/`: 105 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (21 contracts, 42 implementation artifacts, 21 `source-native` design artifacts, 21 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

Variant splits are inferred. End Of Day Balance: level 1 net balances, level 2 a greedy largest-creditor/largest-debtor
settlement. Factory Network: level 1 independent minima (as the preview states), level 2 neighbours in index order may not share
an option index, level 3 the same rule over tree edges. Find Middle Course: level 1 the single chain of the preview, level 2 the
middle courses (left middle for even lengths) of every start-to-end path of a DAG. Find Nearest Exit: level 1 the distance,
level 2 the exit cell with a row-then-column tie rule. File System Collection adds inferred methods (top collections,
parent links, hierarchy totals) to the preview's constructor and direct totals. File System Deletion returns the post-order
sequence of delete calls; File System Directory Size Sum sums directory totals that are at most a limit. Money is integer cents;
timestamps are integers.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`); no frozen file changed afterwards. After the first full run the End Of Day Balance v2
heaps were rekeyed in both languages from (amount, name) to (amount, rank of the name in sorted order), and the JavaScript heap
moved to an Int32Array with inlined comparisons, to bring its heaviest row from 0.63 s to 0.34 s under node --jitless; the
greedy algorithm and its output are unchanged.

## Local checks (author self-check, not qualification)

All 5369 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct class,
with inputs unchanged. A further 26572 seeded Python rows matched the references. The native observers pass on all 253 class
cases in each language with the unchanged easy16 transport. The heaviest case takes 0.34 s per execution under
node --jitless and 0.19 s under python3 (End Of Day Balance v2, `checks.json`). These runs check the code against the author's
own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and,
above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
