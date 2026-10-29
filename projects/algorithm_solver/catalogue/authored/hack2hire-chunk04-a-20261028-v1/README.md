# Hack2Hire chunk04-a: twenty-five authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 25 of their variants, from coordinator
worklist h2h-chunk04-a (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01-a/b, chunk02-a/b/c/d and other chunk04/03 cohorts) are separate; this cohort follows the chunk01-a and chunk02-d layout.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and `preview_content_sha256`, and a stated uncertainty level. Spec text is a
paraphrase in the author's words. No preview text beyond short identifiers is copied. `official_interface` is null everywhere.
No preview was found to describe a different problem than its title.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in both
  languages, standard library only, no I/O, inputs never mutated. Integer results stay below 2**53. Money is handled in
  integer cents (the JavaScript recent-transaction aggregate sums cents in BigInt); the rank in the spanning-tree variant is a
  decimal string decoded with Python int / JavaScript BigInt.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (literal replays, full snapshot copies,
  exhaustive enumeration, quadratic scans, a reflection-principle closed form, naive Pruefer decoding). `cases.py` generates small
  random rows, boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 22 source-free tests
  (hand-worked examples, domain rejections, a closed-form-vs-enumeration check, a rank-to-tree bijection check) plus the
  author-local candidate runner.
- Native classes (9 variants: AccountCreditTracker x2, RequestRouter x3, SocialNetwork x3, SubarrayFirstIterator x1) follow
  requested-22-a, chunk01-a and chunk02-d: a module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids, constructor arguments and void
  methods normalised to null. `test_native_observer.py/.cjs` hold source-free toy controls plus author-local runs.
- `study-content.json` and `study-records/`: 125 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (25 contracts, 50 implementation artifacts, 25 `source-native` design artifacts, 25 approaches with reasoning/coding/validation
  stages and ordered hints), validated against `projects/problem_catalogue/schema.v1.json` by `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

The credit tracker narrows the preview's double credits to integers 0..10^6 so both languages are exact. The request router is a
text command protocol; every command word beyond REGISTER (ROUTE, UP, DOWN, RELEASE), the squared-distance metric and the ERROR
sentinel are inferences. The spanning-tree variant turns "uniform" into a deterministic rank bijection: drawing the rank
uniformly gives a uniform tree, so a sampler can be checked exactly. Recent-transaction times are integer epoch seconds.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed. One post-freeze
change, recorded in `pre-source-reference-freeze.json` and `case-design-summary.json`: the router analytic-maximum row used a
10-digit capacity token, which the frozen spec itself rejects; it became 999999999. No reference, validator or expected-value
rule changed. The JavaScript credit tracker v2 heap was restructured (packed numeric keys, hole-based sifting) for speed under
`node --jitless`; the algorithm is unchanged.

## Local checks (author self-check, not qualification)

All 6707 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct class,
with inputs unchanged. A further 53257 seeded Python rows matched the references. The native observers pass on all 2276 class
cases in each language with the unchanged easy16 transport. The heaviest case takes 0.29 s per execution under
node --jitless and 0.16 s under python3 (`checks.json`). These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above all,
the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
