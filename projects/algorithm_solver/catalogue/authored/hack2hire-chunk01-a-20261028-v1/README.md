# Hack2Hire chunk01-a: thirty authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 16 Hack2Hire coding groups and all 30 of their variants, from coordinator
worklist h2h-chunk01-a (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling chunk01-b
is a separate cohort.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and a stated uncertainty level. Spec text is a paraphrase in the
author's words; no preview text beyond short identifiers is copied. `official_interface` is null everywhere.

Labels used below: **capability** = what the code here does (author-local runs only); **inference** = the spec the
code targets; **claim** = nothing about the official problems is claimed.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis, uncertainty and variant-split
  inference. `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one solution per variant, the same algorithm in both languages,
  standard library only, no I/O, inputs never mutated. Integer results are below 2**53. Delivery costs are exact
  rationals rounded half-up to cents with integer arithmetic.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant. `cases.py` generates small random
  rows, boundary rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 19 reference tests plus
  the author-local candidate runner.
- Native classes (15 variants: BankingSystem x4, DeliverySystem x3, Document x3, TennisGame, TennisSet, FileSystem x2,
  ConnectKGame) follow requested-22-a: module-global class (Python) or a property of the CommonJS `solve` export
  (JavaScript), plus a separate `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`,
  `native_protocol.py` and `native-bindings.json` adapt the direct-class observer to string uids, constructor arity
  (ConnectKGame takes `k`) and void methods normalised to null. Return kinds are checked against the inferred interface.
- `study-content.json` and `study-records/`: 150 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (30 contracts, 60 implementation artifacts, 30 `source-native` design artifacts, 30 approaches), validated by
  `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices for non-deterministic problems

Random ad assignment takes injected `randomIndices`. The concurrent web crawler takes an injected URL-to-links map and
returns a sorted set. Card shuffling takes an injected shuffled deck. Each inferred spec states this.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed. Post-freeze
changes, all recorded in `pre-source-reference-freeze.json` and `case-design-summary.json`: (1) menu maximum row chain
depth 499 -> 199 (node count unchanged; depth 499 overflowed Python recursion in `copy.deepcopy` and the easy16 recursive
encoder); (2) FileSystem maximum row 1500 -> 500 finds (per-case CPU budget; each find must scan its subtree under
arbitrary filters); (3) `test_oracles.py` timing reports the slower of the two executions per case. No reference or
expected-value rule changed.

Candidate algorithms revised for the per-case budget: DeliverySystem v3 keeps per-driver merged unions and a dynamic
range-add/range-max segment tree (O(log T) peak query); BankingSystem L2-L4 keep the spender ranking sorted
incrementally; FileSystem stores full paths at insert.

## Local checks (author self-check, not qualification)

All 5830 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct
class, with inputs unchanged. 28865 further seeded Python rows matched the references. The native observers pass for
all 15 class variants with the unchanged easy16 transport. Heaviest single-execution CPU per case: 0.61 s under
node --jitless and 0.69 s under python3 (`checks.json`). These runs check the code against the author's own inferred
contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and, above
all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
