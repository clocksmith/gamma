# Hack2Hire chunk06-b: twenty-two authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 22 of their variants, from coordinator
worklist h2h-chunk06-b (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01 to chunk05, chunk06-a) are separate; this cohort follows the chunk04-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers and record-format templates is copied.
`official_interface` is null everywhere. No preview was found to describe a different problem than its title.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Every integer stays below 2**53 (the JavaScript job heap packs
  (end, machine) into one number below 2**32).
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (recursive rendering with record rescans,
  fixed-point reachability, union-find parity, regular-expression token scans, explicit candidate sets, literal server logs,
  exhaustive knight-path enumeration, bubble passes, quadratic scans). `cases.py` generates small random rows, boundary rows and
  analytic rows at the inferred maximum bounds. `test_oracles.py` holds 20 source-free tests (hand-worked examples, domain
  rejections, a transcript-identifies-the-secret check over sampled 4-digit secrets) plus the author-local candidate runner.
- No native-class variants: every inferred interface is a function (`solve` plus the inferred wrapper name), so this cohort has no
  `native_harness`, `native_protocol`, `native-bindings.json` or native observer tests.
- `study-content.json` and `study-records/`: 110 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (22 contracts, 44 implementation artifacts, 22 `source-native` design artifacts, 22 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

- Interactive groups (Guess Number, Guess Number II, Guess Number with Delay) are modelled with a server simulated from the hidden
  value passed as an argument. The output is the deterministic guess transcript (or `[secret, calls]`) of a strategy that the
  inferred spec fixes, so outputs compare exactly. The official problems very likely accept any strategy within a query budget;
  the strategies here are modelling choices, not claims about the official checker.
- Guess Number II: responses after the first query ("Hotter", "Colder", "Same") are inferred; the strategy is defined on the set
  of still-consistent targets so the reference can filter that set explicitly while the candidate keeps an interval.
- Format a Task Hierarchy: four variants inferred as cumulative levels (forest; skipping malformed, duplicate and orphaned
  records; outline numbers; completion boxes rolled up from subtasks). Sibling order is record order (inferred).
- Group Chat Mention Counter: the `@all` token is an inference from the preview's "covered by more than one mention token" wording.
- Highlight Phrases: case-insensitive, longest match at each word start, left-to-right, first mapping wins (all inferred).
- Integer to English: ranges 0-9 (stated), 0-999 and 0-2^31-1 (inferred).

## Freeze

References, validators, contracts, design and the case generator were frozen before any candidate file existed
(`pre-source-reference-freeze.json`). One reference bug was found and fixed before the freeze by a hand-worked test: the Game
Machine reference started its maximum at 0 and so ignored all-negative scores. No post-freeze amendments.

## Local checks (author self-check, not qualification)

All 6064 generated rows pass in both languages, through `solve` and through the inferred wrapper, with inputs unchanged. A further
48256 seeded Python rows matched the references. The heaviest case takes 0.15 s per execution under node --jitless (Job
Scheduler, 100000 jobs) and 0.08 s under python3 (Grid Coloring) (`checks.json`). These runs check the code against the author's
own inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above
all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
