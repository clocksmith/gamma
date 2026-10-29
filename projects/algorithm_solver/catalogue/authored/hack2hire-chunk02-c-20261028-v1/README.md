# Hack2Hire chunk02-c: thirty-two authored development pairs over INFERRED specifications

Scope: authored, not qualified. This cohort covers 18 Hack2Hire coding groups and all 32 of their variants, from coordinator
worklist h2h-chunk02-c (2026-10-28). Problem identity is the string uid `hack2hire:<variant id>`. Sibling cohorts
(chunk01-a/b, chunk02-a/b/d) are separate.

## Epistemic status

No official specification was available. Each group has only a partial, group-level public preview
(`data/question_bank/hack2hire/details/<post id>.json`, `payload.data.contentPreview`), with no per-variant text.
The claude-opus-5-5 subagent inferred every spec, interface, bound, variant split and example on 2026-10-28 from the
preview, title and tags. Every contract row says `spec_basis: inferred` and records who inferred it, which preview
fields it used, the preview `response_sha256` and a stated uncertainty level. Spec text is a paraphrase in the
author's words; no preview text beyond short identifiers is copied. `official_interface` is null everywhere.

Labels: **capability** = what the code here does (author-local runs only); **inference** = the spec the code targets;
**claim** = nothing about the official problems is claimed.

Multi-variant groups (Accept-Language x4, Cloud Storage x4, Cloud Cost x3, Crypto Mining x3, and the pairs) carry no
per-variant text at all. Their splits are inferred as cumulative follow-up parts; `inference_uncertainty` says so per row.
The least certain inferences are the Business CSV validator rules (column meanings and every rule are the author's
invention), Account Balance Transfer (rounding and the follow-up), Camera Log Relay (API names), Dasher pay (rate,
canceled orders) and all follow-up variants.

## Files

- `contracts.json`: per variant, the inferred spec, `inferred_interface`, inference basis and uncertainty.
  `assignment.public-safe.json` and `design.json` (reference / candidate design / complexity target) are alongside.
- `python/<variant id>.py`, `javascript/<variant id>.js`: one self-contained solution per variant, the same algorithm in
  both languages, standard library only, no I/O, inputs never mutated. Money and exchange rates use scaled integers
  (Python int, JavaScript BigInt), so every result is exact.
- `semantics/<variant id>-<lang>.json`: per-source semantics with `qualification.status: unknown`.
- `oracles.py`: inferred-domain validators and an independent reference per variant (literal rebuilds, brute-force
  subsets, simple-path DFS with Fractions, minute sweeps, full snapshots). `cases.py` generates boundary rows, 200 seeded
  random rows and analytic rows at the inferred maximum bounds. `test_oracles.py` holds 20 reference tests plus the
  author-local candidate runner.
- Native classes (13 variants: WindowedKeyValueStore, TransactionSystem x2, CameraLogServer, CloudStorage x4,
  CustomerRevenueSystem x2, ConnectFour, InMemoryKVDB, DocumentLibrary) follow requested-22-a as adapted by chunk01-a:
  module-global class (Python) or a property of the CommonJS `solve` export (JavaScript), plus a separate
  `solve(operation_names, argument_lists)` trace adapter. `native_harness.py/.cjs`, `native_protocol.py` and
  `native-bindings.json` use string uids, constructor arguments from the trace's first row, and void methods
  normalised to null.
- `study-content.json` and `study-records/`: 160 `study.record.v1` records per `../hack2hire-worklists-20261028-v1/STUDY-RECORDS.md`
  (32 contracts, 64 implementation artifacts, 32 `source-native` design artifacts, 32 approaches), validated by
  `test_study_records.py`.
- `pre-source-reference-freeze.json`, `checks.json`, `case-design-summary.json`, `manifest.json`, `SHA256SUMS`.

## Modelling choices

Camera Log Relay asks for thread-safe, non-blocking APIs. It is modelled as one deterministic linearised call sequence;
a sequential trace cannot test locking, and the spec says so. Currency Exchange assumes directed rates and no arbitrage
(enforced by the validator), so the best rate is well defined.

## Freeze and amendment

References, validators, contracts, design and the case generator were frozen before any candidate file existed. Later
changes are recorded in `pre-source-reference-freeze.json`: (1) four analytic-maximum rows were resized for the per-case
CPU budget, and each new expectation was re-checked against the unbudgeted reference; (2) the CloudStorage L2-L4 design
entry now describes the sorted name index findFile uses. No reference, validator or expected-value rule changed.

## Local checks (author self-check, not qualification)

All 6543 generated rows pass in both languages, through the trace adapter and through the inferred wrapper or direct
class, with inputs unchanged. Every analytic-maximum expectation except the mining and FX rows was also recomputed by the
unbudgeted reference. The native observers pass for all 13 class variants with the unchanged easy16 transport. Heaviest
case: 0.68 s under python3 and 0.64 s under node --jitless. Each figure covers both executions of the case (adapter plus
wrapper/class), so `checks.json` overstates a single execution. These runs check the code against the author's own
inferred contract only. Official ABI, effects, limits and correctness still need the coordinator's isolated runner and,
above all, the official specifications. Qualification status is unknown everywhere.

```sh
python3 test_oracles.py
python3 test_native_observer.py
python3 test_study_records.py
```
