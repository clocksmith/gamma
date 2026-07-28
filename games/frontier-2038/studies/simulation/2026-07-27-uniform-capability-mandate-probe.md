# Uniform-Capability Mandate probe

Date: 2026-07-27  
Evidence label: simulation  
Verdict: reject the candidate; making all Capability thresholds worth 1 Mandate
does not correct Capability Rusher dominance

## Identity

- Raw local report:
  `20260727T212828206Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-uniform-capability-mandate-v1-20260727-15974x4-unified-matrix-cli.json`
- Report SHA-256:
  `9b4aa3a1ae518686a765cb5c1d0e3a390ee2032afd3a1a45551d11f68f142c04`
- Source commit:
  `e15b7578b1ec75976de1e821a2d2597a7eae0185`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `uniform-capability-mandate-v1`
- Root seed: `m3t4-uniform-capability-mandate-v1-20260727`
- Canonical matches: `7,952`
- Candidate matches: `7,952`
- Bounded adversarial matches: `70`
- Matched common-seed pairs: `7,952`
- Unmatched pairs: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

## Candidate

Every Capability threshold changed from 2 Mandate to 1. Capability still
controlled Deploy requirements and AGI eligibility. No other rule changed.

## Results

The candidate halved all Capability-threshold scoring and reduced Demis
Hassabis:

- two players: `64.73%` to `62.62%`;
- three players: `47.84%` to `43.92%`;
- four players: `35.07%` to `31.95%`; and
- six players: `20.17%` to `18.11%`.

The general strategy problem remained:

- four-player Capability Rusher increased from `37.50%` to `38.93%`;
- five-player Capability Rusher fell from `33.43%` to `31.89%`; and
- six-player Capability Rusher fell from `31.33%` to `29.90%`.

At four players its posterior uplift increased from `12.39` to `13.81`
percentage points above expected. The candidate therefore removed public
Capability points without removing the repeatable strategic engine. It also
left Demis highly advantaged at two and three players.

Declarations remained rare and essentially unchanged: `17` canonical versus
`16` candidate. Both arms stayed below the forced-no-op validity ceiling and
reported no integrity violations.

## Interpretation

Public Capability scoring is not the primary cause. Capability Rusher converts
Research into early Deploys, then receives both Customer Mandate and recurring
Customer income. The next one-lever probe therefore restores canonical
Capability scoring and changes only Customer Mandate from 2 to 1. Customer
income, Capability requirements, and Deploy costs remain unchanged.

## Surface audit

- Canonical semantic graph and numeric values: unchanged; candidate rejected.
- Rulebook, cards, reference aids, and browser prototype: unchanged.
- Simulation engine: retains the experimental lever for reproducibility.
- Tests: retain direct coverage of the rejected lever.
- Playtest documentation: this receipt records the rejection.
- Immutable release: none.
