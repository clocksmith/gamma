# Hack2Hire chunk02-b: 26 newly authored development pairs over INFERRED specifications

Scope: authored, not qualified. 18 Hack2Hire groups, 26 variants (worklist chunk02-b, 2026-10-28). Identity is the
string uid `hack2hire:<variant id>`; sources are `python/<variant id>.py` and `javascript/<variant id>.js`.

Epistemic class: every specification and interface here is an INFERENCE by the claude-opus-5-5 subagent on
2026-10-28. The basis is the public group preview (`payload.data.contentPreview`, partial and group-level), the
title, `algorithmTags` and the variant ids in `codingQuestions` under `data/question_bank/hack2hire/details/`. No
solution, full-content or locked endpoint was read. `contracts.json` paraphrases each inferred spec in the author's
own words, records `spec_basis: inferred` and the preview `response_sha256`, and copies no preview text beyond
identifiers. Sibling variants of one group (ORG 1-4, CART 1-3, TODO 1-2, NARY 1-2, MAZE 1-2) are distinguished only
by inference, because the previews are group-level.

Independent reference code, inferred-domain validators, contracts, case generator and design were frozen before
any candidate file existed (`pre-source-reference-freeze.json`). One analytic maximum expectation in `cases.py`
(PCT, percentile 1) was wrong in the freeze. It was corrected after the first candidate run and is recorded under
`amendments` in that file. References use different algorithms from the candidates: sibling-position sort keys,
ancestor-chain membership, Decimal sums, transaction expansion, Floyd-Warshall, brute subset matching, literal
negation, quadratic prefix tests, exhaustive 2/3-character cuts with re-encoding, per-cell line-of-sight tests,
regular-expression parsing, backward DFA state sets, per-cut flood fills, recursive trees, level lists, prefix
Counters, list snapshots, transitive closures and signature expansion. Maximum-domain rows carry analytic
expected values. There is no language-agreement oracle.

Modelling choices: printing (ORG) is modelled as returning lines. The URL maze `request` helper is an injected map
`url -> {message, next[, headers, requiredHeaders]}`, so it is deterministic and does no I/O. The DFA's fixed
diagram is not in the preview, so the automaton is injected (a generalisation, not the original question). Snapshot
iterators are integer handles so the trace stays JSON.

Class variants (SnapshotSet, ToDoList x2, FunctionLibrary) are native classes: module globals in Python and
properties of the callable CommonJS `solve` export in JavaScript. `solve(operation_names, argument_lists)` is a
separately declared trace adapter, with null for construction and void methods. `native_harness.py/.cjs` dispatch
the original class directly with no solve fallback; `native-bindings.json` pins the unchanged easy16 transport and
judge sandbox. Function variants use canonical `solve` plus an inferred `Solution` method (Python) or a named
function export (JavaScript).

The author ran their own candidates locally after the freeze. `test_oracles.Candidates` covers all 5,783 generated
and maximum cases per language (python3 and `node --jitless`), plus the wrappers and native classes. Results and
single-sample CPU times are in `checks.json`; the heaviest case is 0.20 s (python3) and 0.38 s (node --jitless).
That is author self-checking against an inferred contract, not isolated or independent qualification. The
qualification status is unknown everywhere.

`study-records/` holds `study.record.v1` contract, approach and artifact records built from these files and
`study-content.json`, validated by `test_study_records.py`.

```sh
python3 test_oracles.py
python3 test_study_records.py
```
