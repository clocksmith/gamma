# Clean canonical 3/4/5 deterministic baseline

**Date:** 2026-08-01  
**Evidence label:** Simulation  
**Status:** Valid baseline; non-promotional and not a rule-change recommendation.

## Registered execution

- Registration: `clean-canonical-3-4-5-v1` under
  `unified-seven-axis-matrix-v1`; it records `usesCommittedDefault: true`.
- Exact source: commit `db06a08fe8b28214aad746e9f00447514a9fdadf`,
  `sourceDirty: false`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Engine fingerprint:
  `sha256:21b899fe56af0a74682cb9eed0f6bb4013a3aff53cf47ed8f1eacde4a0675637`.
- Root seed: `frontier-2038-clean-canonical-2026-08-01`.
- 960 deterministic matches: 286 at three players, 312 at four, and 292
  at five. The batch projection used seven bounded worker threads for initial
  cells and stable `matrix_cell_then_match_index` merging.
- Player policies: the seven authored profiles, rotating rosters; weighted,
  greedy, and the two alternating backend regimes; variable and fixed Mandate
  modes; negotiation enabled. No LLM providers were used.
- Raw report:
  `evidence/studies/simulation/20260801T155804748Z-unified-matrix-audit-0-8-27-fc8bd0450b92-frontier-2038-clean-canonical-2026-08-01-960x4-unified-matrix-cli.json`.
  SHA-256:
  `ab0f84068b9f6f0b2dfc1b9a032c5e699199a75c32ec1541f78dd1d6335f4af8`.

## Findings

- Procedural integrity: zero violations; zero policy fallbacks; forced-no-op
  rate 0.019% overall, below the 3% limit.
- The four-player authoritative configuration passed its observed faction-range
  screen at 8.49 points; five players passed at 9.04 points. Three players
  failed the provisional 15-point screen at 18.23 points.
- The multiplicity-safe precision target was not reached. No partially pooled
  faction or pairwise dominance cell was detected, but that is not evidence of
  balance at the registered precision.
- Winning-path and opening diversity checks passed at every supported player
  count.
- The intended AGI route is not exercised by this deterministic policy matrix:
  it produced zero legal declaration windows and zero declarations at three,
  four, and five players. This is a policy-coverage gap, not evidence that the
  rulebook forbids declaration or that the game is balanced around it.

## Interpretation and next evidence

This report is valid evidence that the current deterministic engine runs the
registered canonical matrix cleanly. It does **not** promote the rules. Before
any rules change, run a clean common-seed three-player faction/seat isolation
study to explain the range failure, and run a declaration-focused deterministic
scenario with policies that actually pursue Grid-Ready and AGI. Keep any later
strict LLM field separate as robustness evidence with zero fallback.

## Affected surfaces

- Canonical rulebook: no change.
- Semantic content and generated data: no change.
- Simulator and browser prototype: no change.
- Reference/player aids: no change.
- Tests: no change.
- Playtest documentation: this receipt records simulation evidence only; no
  human-play claim is made.
