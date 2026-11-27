# Strategic-unsolvability audit calibration

Date: 2026-07-27  
Disposition: calibration only; rejected as balance or promotion evidence

## Identity

- Raw local report:
  `studies/simulation/20260727-strategic-unsolvability-audit-v1.json`
- SHA-256:
  `305255161f873745c75363ec0ac20bb5470c237a2bc77cb31f2e3a91e072194d`
- Source commit: `dde498dfefb8faa362917149e1117e791bc2eb25`
- Source dirty: `false`
- Executable game: `0.5.0`
- Engine: `selected-rules` `0.7.0`, coverage `lean-grid-ready-v5`
- Report schema: `5`
- Contract: `strategic-unsolvability-v1`
- Seed: `m3t4-strategic-audit-20260727`
- Player count: `4`
- Backends: deterministic weighted only
- Pairing design: all 21 unordered authored-persona pairs
- Runs per matchup or candidate evaluation: `8`
- Mutation search: 2 generations × 3 candidates
- LLM decisions: none

## Intended hypothesis

The first audit attempted to determine whether authored personas survived a
complete pairwise league, bounded best-response mutation, counter-response
mutation, and holdout evaluation without exceeding provisional dominance,
concentration, or integrity bounds.

## Observed output

- Pair coverage: `100%`
- Action entropy: `0.9053` — inside the provisional bound
- Opening entropy: `0.6446`
- Largest opening share: `0.5313`
- Largest observed pairwise placement rate: `0.75`
- Largest best-response uplift: `0.50`
- Smallest counter-response recovery: `0`
- Largest holdout collapse: `0.625`
- Policy fallbacks: `0`
- Aggregated integrity violations: `4`
- Automated disposition: `rejected_by_automated_gate`
- Promotion eligible: `false`

## Why the extrema are not balance evidence

The audit took the worst point estimate across many eight-run cells. The
maximum of many noisy estimates is upward-biased, so the reported faction,
seat, persona, interaction, opening, and path extrema exaggerate evidence
against the candidate. It published no uncertainty interval, performed no
partial pooling, did not control repeated adaptive looks, and did not retain
the individual integrity-violation details in the aggregate report.

The audit also treated authored cooperative roles as experimental categories.
Those policies establish route feasibility but cannot represent Cosmic-style
agreements that form, break, and reform under self-interest. Decision backend
was not rotated as a first-class factor.

## Decision

No game rule, faction value, Grid-Ready requirement, Power value, score, or
threshold changes as a result of this report. The report is retained to
calibrate and regression-test the replacement evidence system.

## Required replacement

Use one seven-factor sampling frame: rules configuration, player count, faction,
seat, strategy, RNG/mandate configuration, and decision backend. Cooperation
must be measured as an outcome. Publish partially pooled estimates and
intervals, enforce multiplicity-safe sequential stopping, rotate backends, and
reserve metered LLM calls for a preregistered negotiation holdout.

## Surface audit

- Canonical rulebook: no change.
- Semantic game graph and numeric values: no change.
- Browser game implementation: no change.
- Reference cards and player aids: no change.
- Simulator and report contract: replacement required in the next controlled
  implementation.
- Simulation Lab: replacement required in the next controlled implementation.
- Tests: replacement coverage required.
- Evidence documentation: this receipt records the invalid inference boundary.
