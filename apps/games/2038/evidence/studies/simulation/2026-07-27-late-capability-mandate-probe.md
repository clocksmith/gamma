# Late-Capability Mandate probe

Date: 2026-07-27  
Evidence label: simulation  
Verdict: reject the candidate; reducing only Capability 9 and 12 to 1 Mandate
does not correct Capability Rusher dominance

## Identity

- Raw local report:
  `20260727T210906419Z-unified-matrix-audit-0-7-3-362efcd2f217-m3t4-late-capability-mandate-v1-20260727-15974x4-unified-matrix-cli.json`
- Report SHA-256:
  `b487c8d5a419c12da650365b0d687dc4919ec251956ffcfdd5c5ffe5e35680bc`
- Source commit:
  `c5a262647e9434f20c850db0725ae849e172a718`
- Source dirty: `false`
- Executable: `0.7.3`
- Engine: `selected-rules` `0.9.5`
- Preregistration: `late-capability-mandate-v1`
- Root seed: `m3t4-late-capability-mandate-v1-20260727`
- Canonical matches: `7,952`
- Candidate matches: `7,952`
- Bounded adversarial matches: `70`
- Matched common-seed pairs: `7,952`
- Unmatched pairs: `0`
- Integrity violations: `0`
- Policy fallbacks: `0`
- LLM calls: `0`

Both arms crossed player counts two through six, fixed and variable Mandates,
balanced faction and Initiative rotation, all authored personas, and all four
registered deterministic backend regimes.

## Candidate

The candidate retained 2 Mandate at Capability 3 and 6 but reduced Capability
9 and 12 from 2 Mandate to 1. No other rule changed.

## Results

The scoring change worked mechanically. Aggregate Capability-9 Mandate fell
from `36,500` to `18,201`, and Capability-12 Mandate fell from `17,090` to
`8,541`. It reduced Demis Hassabis’s aggregate win share by `2.746` percentage
points and mean score by `1.251`.

It did not solve the nominated strategic problem:

- at four players, Capability Rusher rose from about `37%` to `38%`;
- at five players, it fell only from about `32%` to `31%`;
- at six players, it fell only from about `32%` to `31%`; and
- its four-player posterior uplift increased from `11.61` to `12.39`
  percentage points above the expected share.

The candidate also reduced the four-player Infrastructure Compounder from
about `31%` to `27%`, while moving Market Maximalist and Balanced Operator
upward. The main Capability lane therefore retained its practical lead rather
than yielding to a broader competitive field.

The candidate recorded `6` declarations versus `5` in canonical and stayed
below the forced-no-op validity ceiling. Those rare-count differences are not
interpretable as an AGI effect.

## Decision and surface audit

- Canonical semantic graph and numeric values: unchanged; candidate rejected.
- Rulebook, cards, reference aids, and browser prototype: unchanged.
- Simulation engine: retains the experimental lever for reproducibility.
- Tests: retain direct coverage of the rejected lever.
- Playtest documentation: this receipt records the rejection.
- Immutable release: none.

The next registered probe tests one stronger but still singular scoring
contract: every Capability threshold is worth 1 Mandate. It preserves
Capability’s functional role in Deploy and AGI while testing whether double
rewarding the same progression through both Capability and Customers is the
actual strategic imbalance.
