# Single-Generator Default contract smoke

**Date:** 2026-08-08 local / 2026-08-09 UTC  
**Evidence label:** Simulation / clean common-seed candidate diagnostic  
**Status:** Valid execution and integrity evidence. The candidate remains
inactive and failed the provisional automated bounds; this report does not
authorize promotion.

## Registered execution

- Candidate contract:
  [`experimental/single-generator-default.md`](../../../experimental/single-generator-default.md).
- Rules configurations:
  [`experimental/data/single-generator-default.rules-configurations.json`](../../../experimental/data/single-generator-default.rules-configurations.json).
- Preregistration ID and root seed:
  `single-generator-default-contract-smoke`.
- Exact source commit:
  `13d56584982c0a48f4c1cd0492f0c39f230903b4`, with
  `sourceDirty: false`.
- Executable game `0.9.2`, selected-rules engine `0.11.2`, and physical rules
  candidate `0.6.0-rc.3-test`.
- Ruleset fingerprint:
  `sha256:bed2738e1280af752b8c134c6054342c7c653f2425f4b91e7e78a5c4e7964036`.
- Engine fingerprint:
  `sha256:0e67164086a58ef1aaffbb28cfc97bf1239ff2a85a3e1bb5745137dd36bec74c`.
- Variant fingerprint:
  `sha256:fecf8657f02c63e810b1a22d6f01982f7d60633521e8e296ee590ba1402f2c7b`.
- Raw local archive:
  `evidence/studies/simulation/20260809T022742421Z-unified-matrix-audit-0-9-2-bed2738e1280-single-generator-default-contract-smoke-168x4-single-generator-default-contract-smoke.json`.
  Its SHA-256 is
  `663a75b6983a7484ca5a6d3fbc201f8c562e532bddb7a48dafed1838fd717900`.

## Scope and result

The smoke completed 168 deterministic matches: 84 canonical and 84 candidate.
Each arm contributed 28 matches at three, four, and five players. The matrix
used fixed Mandates, all registered weighted/greedy backend regimes, rotating
strategy rosters, four worker threads, and batch projection. It produced 84
exact common-seed pairs, zero unmatched pairs, zero standing mismatches, and
zero integrity violations.

This is minimum execution coverage, not the protocol's full evidence matrix.
It deliberately omits variable Mandates, the adaptive precision budget, the
adversarial slice, and human sessions.

The automated promotion gate returned `provisional_bounds_failed`. The
candidate's observed faction win-share range was `0.25` at three players and
`0.17857142857142855` at five players, both above the registered `0.15`
threshold. Four players passed that screen at `0.08928571428571427`. The
registered precision target was not reached. Forced no-ops remained below the
registered limit, and no policy fallback occurred.

## Interpretation and disposition

The candidate is executable, deterministic, replay-compatible, and suitable
for a larger isolated study. The smoke does not show that it is balanced or
teachable. The three- and five-player range failures are signals to measure,
not correction instructions: exposure is sparse, confidence sequences are
wide, and only fixed Mandates were used.

Disposition: retain as a diagnostic candidate. Do not add it to
`playRuleModules`, Default Game, Advanced Play, player-facing rules, or physical
component counts. The next automated run must use the full registered
three/four/five-player matrix with fixed and variable Mandates and preserve
common seeds. Human sessions must independently measure explanation errors,
Energy-location contention, negotiation quality, agency, and downtime before
any acceptance decision.

## Affected-surface audit

- Canonical Default and Advanced mechanics: no change; the candidate requires
  one explicit `singleGeneratorRule` overlay.
- Candidate execution: one ordinary Generator; Energy location fixes source
  and construction cost; dedicated starting-grid Power cannot be reassigned;
  malformed contracts fail before play.
- Player-facing rules, reference cards, browser profile selector, and physical
  component counts: no candidate activation and no candidate copy projection.
- Release identity: executable `0.9.2` and physical candidate
  `0.6.0-rc.3-test` record the new inactive engine path without a physical rule
  change.
- Human evidence: absent. No teachability, negotiation, or play-duration claim
  is made.
