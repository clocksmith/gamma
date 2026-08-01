# AGI route coverage study

**Date:** 2026-08-01

**Evidence label:** Simulation / deterministic coverage

**Status:** Valid complete coverage study; canonical declaration route reached;
coverage remains sparse and no rule change selected.

## Registered execution

- Preregistration: `agi-route-coverage-v1`, committed before results at
  `b85a3fbd`.
- Exact source: commit `bff79d457698ba9633125d689fea76e9613b6e3a`,
  `sourceDirty: false`.
- Executable game `0.8.30`; selected-rules engine `0.10.29` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Four separately seeded four-player fields of 100 games each, batch
  projection, four workers per field, explicit profiles/backends, canonical
  rules, and variable Mandate.
- Total: 400 games and 1,600 player opportunities. There were zero integrity
  violations, zero policy fallbacks, and one forced no-op across all fields.
- No LLM provider was enabled or called.

## Funnel results

| Field | Core met | Needed external Power | Received offer | Grid-Ready | Legal window | Declared |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Broker-heavy greedy | 192 | 18 | 42 | 2 | 1 | 1 |
| Broker-heavy weighted | 80 | 1 | 69 | 3 | 0 | 0 |
| Claimant-only greedy | 202 | 41 | 0 | 0 | 0 | 0 |
| Claimant-only weighted | 137 | 17 | 32 | 3 | 0 | 0 |
| **Total** | **611** | **77** | **143** | **8** | **1** | **1** |

The broker-heavy greedy field completed 77 Power trades, 27 of them causally
necessary, and produced the sole legal declaration window and declaration in
Round IV. The claimant-only greedy field produced no Power trades and no
Grid-Ready players despite 202 core-requirement hits. This isolates a policy
composition boundary: AGI candidates alone do not create the supplier behavior
that the route requires.

The four raw local reports and SHA-256 hashes are:

- `evidence/studies/simulation/2026-08-01-agi-route-coverage-v1.broker_field_greedy.raw.json` —
  `f38af26ef7d8136332dbabffca102c8ad93ca6fa7d9c6dedbd96c524a96ef7e0`.
- `evidence/studies/simulation/2026-08-01-agi-route-coverage-v1.broker_field_weighted.raw.json` —
  `182158e01fc8b853c91b66ff27c27c30425d226b0273457db42183a753931eae`.
- `evidence/studies/simulation/2026-08-01-agi-route-coverage-v1.claimant_field_greedy.raw.json` —
  `2cc2d1e28a2c29423f4d869dd02624b026df38c625314bc3d74795920cf3d2e7`.
- `evidence/studies/simulation/2026-08-01-agi-route-coverage-v1.claimant_field_weighted.raw.json` —
  `dd802c42e64858cd3b74cc601eb46718f2e2f4d69dd18ccf53045d5309cef4a8`.

## Interpretation and decision

- The canonical Grid-Ready and declaration engine route is reachable. The
  ordinary matrix's zero legal windows was a coverage failure, not proof of an
  impossible route.
- Reachability is still sparse: one legal window among 1,600 player
  opportunities. This study proves reachability, not AGI-route balance or a
  desirable declaration rate.
- Supplier composition and deterministic policy behavior explain a large part
  of the route drought. No AGI threshold, cost, reward, Grid-Ready, Power, or
  timing rule should change from this coverage study.
- A later AGI balance study must deliberately oversample valid declaration
  states or use a registered scenario fixture; ordinary tournament frequency
  is too low for an outcome comparison.

## Affected-surface audit

- Canonical rulebook, AGI requirements, and Power rules: no change.
- Semantic content and generated gameplay data: no change.
- Simulator and browser prototype: no change; the existing route was exercised.
- Reference cards and player aids: no change.
- Authored deterministic policies: no change in this study; the broker/claimant
  composition difference is a future policy-coverage question.
- Tests: no change; the frozen release had already passed 167 of 167 tests and
  the release gate.
- Playtest protocol: retain deliberate Grid-Ready and declaration-window
  observation. Do not treat an ordinary playtest with no declaration as neutral
  AGI evidence.
