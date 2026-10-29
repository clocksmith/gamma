# Hack2Hire chunk04-b: twenty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 20 of their variants, from coordinator
worklist h2h-chunk04-b (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01-a/b, chunk02-a/b/c/d, chunk04-a) are separate; this cohort follows the chunk01-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

The least certain inferences (uncertainty "very high" in `contracts.json`):

- Compute Server Load Scores: the preview names three stress categories but no rule. Volume +1, intensity 0/2/5 and a
  60-second burst +3 are the author's own invention, made only to have a testable contract.
- Correct Bedroom Counts from Descriptions: the keyword set, the word definition and the conflict rule are inferred.
- Calculate Equation Expression level 3 (undefined or cyclic references give null) and Chat Message Events Aggregation
  level 3 (distinct users per chat): both level splits are guesses.

Build Binary Tree From Character Counts (Huffman-style merge with fixed tie-breaks), Call Elevator (moving-elevator rules)
and Coins and Energy (1 energy per move) are rated "high". None of the 16 previews reads as a different problem from its title.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Integer results stay below 2**53. Color a Row of Houses
  is computed modulo 1000000007 with BigInt in JavaScript.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (linear scans, literal simulation,
  exhaustive enumeration, fixed-point evaluation, a 2x2 matrix power, Miller-Rabin, lookaround regexes). `cases.py` generates
  small random rows, boundary rows and rows at the inferred maximum bounds. `test_oracles.py` holds 19 source-free tests
  (hand-worked examples, domain rejections, a matrix-vs-enumeration check for the house colourings, a tree-invariant check)
  plus the author-local candidate runner.
- Native classes (3 variants: ChatEventAggregator levels 1-3) follow requested-22-a, chunk01-a and chunk02-d:
  a module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` adapt the direct-class observer to string uids; the void `recordEvent` is normalised to null.
  `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 100 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (20 contracts, 40 implementation artifacts, 20 `source-native` design artifacts, 20 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

The chat aggregator takes a logical-time call sequence: every call carries a timestamp, timestamps never decrease across
calls, and history outside every future window is evicted. Elevator floors and storage request fields are decimal strings,
as the previews show; they are parsed to integers.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). Nothing in those files changed afterwards. The Python bedroom tokeniser was rewritten
from a per-character loop to one regex split, with the same word definition, because it was the slowest case.

## Local checks (author self-check, not qualification)

All 5079 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct
class, with inputs unchanged. A further 25185 seeded Python rows matched the references. The native observers pass on all
762 class cases in each language with the unchanged easy16 transport. The heaviest case takes 0.09 s per execution under
node --jitless and 0.16 s under python3 (`checks.json`). These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all,
the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
