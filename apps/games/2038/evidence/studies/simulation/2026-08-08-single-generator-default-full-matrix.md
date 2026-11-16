# Single-Generator Default full matrix

**Date:** 2026-08-08 local / 2026-08-09 UTC  
**Evidence label:** Simulation / clean common-seed candidate diagnostic  
**Status:** Valid full automated execution and integrity evidence. All registered
observed checks passed, but the precision gate did not. The candidate remains
inactive and this report does not authorize promotion.

## Registered execution

- Candidate contract:
  [`experimental/single-generator-default.md`](../../../experimental/single-generator-default.md).
- Rules configurations:
  [`experimental/data/single-generator-default.rules-configurations.json`](../../../experimental/data/single-generator-default.rules-configurations.json).
- Preregistration ID and root seed:
  `single-generator-default-full-matrix-v1`.
- Exact source commit:
  `6b0cebe15ee98dc367328e8d0b37fad5b5d7fad8`, with
  `sourceDirty: false`.
- Executable game `0.9.2`, selected-rules engine `0.11.2`, and physical rules
  candidate `0.6.0-rc.3-test`.
- Ruleset fingerprint:
  `sha256:bed2738e1280af752b8c134c6054342c7c653f2425f4b91e7e78a5c4e7964036`.
- Engine fingerprint:
  `sha256:0e67164086a58ef1aaffbb28cfc97bf1239ff2a85a3e1bb5745137dd36bec74c`.
- Canonical configuration fingerprint:
  `sha256:a332b0b1e9a2b826632a0c7b9df5a62e6b221cb4773d73a3a04df31229360ead`.
- Candidate configuration fingerprint:
  `sha256:943825fe1c976546ef81187370b859246017608a5be757d910ef1a71924c8a56`.
- Experiment-matrix fingerprint:
  `sha256:fecf8657f02c63e810b1a22d6f01982f7d60633521e8e296ee590ba1402f2c7b`.
- Raw local archive:
  `evidence/studies/simulation/20260809T024540004Z-unified-matrix-audit-0-9-2-bed2738e1280-single-generator-default-full-matrix-v1-958x4-single-generator-default-full-matrix-v1.json`.
  Its SHA-256 is
  `9069e05cdca3c4cb400c68d1c5c134a9c43bbbb6d8d437e4b8541584d8208d4a`.

## Scope and integrity

The study completed 958 deterministic runs: 888 balance-authority matches and
70 diagnostic adversarial matches. The balance matrix contained 444 canonical
and 444 candidate matches, producing 444 exact common-seed pairs with zero
unmatched pairs, zero standing mismatches, and zero integrity violations.

Both fixed and variable Mandates were covered at three, four, and five players.
Each arm supplied 112 three-player, 156 four-player, and 176 five-player
matches. The matrix rotated the registered strategy rosters through homogeneous
and alternating weighted/greedy backend regimes, used four worker threads, and
reserved the registered adversarial population. No policy fallback occurred.

All 25 registered observed checks passed. Candidate faction win-share ranges
were `0.0580357142857143` at three players, `0.1432253800396563` at four, and
`0.11764705882352938` at five, each below the `0.15` ceiling. Candidate forced
no-op rates remained below `0.009` at every supported player count. Opening,
action, and winning-path diversity also remained within their registered bounds.
No credible dominance or metacycle was identified.

## Precision and causal signals

The automated verdict was `insufficient_precision`. The registered target
half-width was `0.12`; the maximum core half-width remained `0.5` after the
preregistered match ceiling. Every aggregate faction win-share interval for the
paired candidate comparison crossed zero. The study therefore establishes
legal execution and observed-bound compatibility, not balance equivalence.

The raw outcomes expose a negotiation risk that requires direct study. Emergent
cooperation fell from `0.3581081081081081` in the canonical arm to
`0.21396396396396397` in the candidate arm. Accepted Power offers fell from 191
to 109. Grid-Ready events increased from 2 to 17, but neither arm produced a
legal AGI declaration window or declaration. These are descriptive paired-arm
signals, not registered inferential conclusions, and they cannot support a
claim that negotiation or AGI play improved.

## Interpretation and disposition

Disposition: retain as a diagnostic candidate. Do not add it to
`playRuleModules`, Default Game, Advanced Play, player-facing rules, or physical
component counts. The earlier provisional three- and five-player range failures
did not reproduce in this broader matrix, but the required precision and human
approval gates remain open.

Human sessions must now compare canonical and candidate games for setup and
source-selection errors, Energy-location contention, Power negotiation quality,
perceived agency, downtime, and faction recall. If those sessions justify
continuing, the next automated preregistration must make cooperation and Power
trade retention explicit promotion metrics and allocate enough marginal
exposure to reach its declared precision target. Candidate combinations remain
forbidden while this isolated lever lacks a disposition that authorizes them.

## Affected-surface audit

- Canonical Default and Advanced mechanics: unchanged; the candidate still
  requires the explicit `singleGeneratorRule` overlay.
- Candidate execution: one ordinary Generator; Energy location fixes source and
  construction cost; dedicated starting-grid Power cannot be reassigned;
  malformed contracts fail before play.
- Player-facing rules, reference cards, browser profile selector, and physical
  component counts: no candidate activation and no candidate copy projection.
- Release identity: unchanged by this evidence-only receipt.
- Human evidence: absent. No teachability, negotiation-quality, agency,
  play-duration, or component-reduction claim is made.
