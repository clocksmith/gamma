# Customer-Mandate probe

Date: 2026-07-27  
Evidence label: simulation  
Verdict: reject the candidate; reducing Customer Mandate to 1 weakens Market
play without correcting Capability Rusher dominance

## Identity

- Raw local report:
  `20260727T214554195Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-customer-mandate-one-v1-20260727-15974x4-unified-matrix-cli.json`
- Report SHA-256:
  `2fe155c63cbd1637c053f5d1ed6bc4990f1375e5e0d8f3f0415d4fca29fa1cf9`
- Source commit:
  `29876f27cbb05b1c0015b25b93389e2729972ce6`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `customer-mandate-one-v1`
- Root seed: `m3t4-customer-mandate-one-v1-20260727`
- Canonical matches: `7,952`
- Candidate matches: `7,952`
- Bounded adversarial matches: `70`
- Matched common-seed pairs: `7,952`
- Unmatched pairs: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

## Results

The candidate halved Customer Mandate without changing Customer income,
requirements, or AGI eligibility. It did not correct the nominated strategy:

- four-player Capability Rusher: `37.45%` canonical, `37.55%` candidate;
- five-player: `35.26%` canonical, `35.18%` candidate; and
- six-player: `30.31%` canonical, `31.99%` candidate.

Market Maximalist fell from `28.63%` to `25.33%` at four players, from `20.80%`
to `17.92%` at five, and from `17.78%` to `14.65%` at six. Infrastructure
Compounder rose at three through six players. Jensen Huang also rose from
`29.36%` to `31.15%` at five players.

The change therefore weakened the intended adoption lane, strengthened an
alternative engine, and left the Capability loop intact. It is rejected.
Declarations were identical at `9` per arm. Both arms remained below the
forced-no-op ceiling and had no integrity violations.

## Strategy interpretation

Across canonical four-player head-to-head cells, Capability Rusher is strong
but not uncounterable. Under homogeneous greedy play, Infrastructure
Compounder beat it `53.75%` to `46.25%`. Other backend/matchup cells also cross
50% in both directions. Its aggregate lead is driven partly by crushing weak
authored personas, especially Trust Governor and Power Broker, rather than by
an invariant rules exploit.

Accordingly, no global scoring cut is selected. Strategy-profile evolution and
counter-strategy quality are evidence-harness work, while the persistent
faction extremes are proper candidates for physical-rule probes.

## Surface audit

- Canonical semantic graph and numeric values: unchanged; candidate rejected.
- Rulebook, cards, reference aids, and browser prototype: unchanged.
- Simulation engine: retains the experimental scoring lever for
  reproducibility.
- Tests: retain direct coverage of the rejected lever.
- Playtest documentation: this receipt records the rejection.
- Immutable release: none.
