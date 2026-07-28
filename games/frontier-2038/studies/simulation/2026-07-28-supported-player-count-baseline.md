# Supported player-count baseline

Date: 2026-07-28  
Evidence label: simulation matrix  
Verdict: the three-to-five-player executable is valid and fully covered, but
the registered precision target was not reached; isolate faction effects
before changing a physical rule

## Identity

- Raw local report:
  `20260728T021345914Z-unified-matrix-audit-0-8-0-7b491dc09736-m3t4-supported-player-count-baseline-v1-fresh-20260728-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `8479e651b26bed722f1bd5edfa5d36859ec0a2d0d8d8d5aa489288d1d427cfe3`
- Source commit:
  `ea773fa8c3e48842d17c3147cb49f958f505548e`
- Source dirty: `false`
- Executable: `0.8.0`
- Engine: `selected-rules` `0.10.0`
- Coverage: `three-to-five-grid-ready-v1`
- Physical candidate: `0.5.0-rc.1-test`
- Preregistration: `supported-player-count-baseline-v1`
- Root seed:
  `m3t4-supported-player-count-baseline-v1-fresh-20260728`
- Matrix matches: `11,928`
- Bounded adversarial matches: `70`
- LLM calls: `0`

The preceding evolved-strategy holdout seed is retired and did not select a
correction for this candidate.

## Validity

- Three-player matches: `4,076`
- Four-player matches: `3,968`
- Five-player matches: `3,884`
- Integrity violations: `0`
- Policy fallbacks: `0`
- Forced-no-op rate: `0.3872%`, below the `3%` ceiling
- Registered homogeneous dominance cells: `0`
- Registered pairwise dominance cells: `0`
- Credible registered meta cycles: `0`
- Matrix status: `inconclusive_precision_not_reached`
- Maximum core confidence-sequence half-width: `0.1728`, above the registered
  `0.12` target

These results validate execution and coverage. They do not prove faction,
strategy, or matchup balance.

## Count-specific faction findings

Partially pooled faction win rates across the full backend frame were:

| Faction | 3 players | 4 players | 5 players |
| --- | ---: | ---: | ---: |
| Sam Altman | 22.85% | 16.40% | 12.89% |
| Mark Zuckerberg | 30.81% | 21.59% | 18.27% |
| Demis Hassabis | 49.90% | 38.14% | 26.38% |
| Elon Musk | 20.95% | 16.53% | 12.00% |
| Dario Amodei | 36.62% | 29.64% | 22.97% |
| Jensen Huang | 38.15% | 27.68% | 27.77% |

These are diagnostic rates conditional on faction appearances, not a
six-row share that should sum to 100%. Demis is the clearest concern at three
and four players. Jensen’s five-player result remains consistent with
opponent-count scaling. Sam and Elon remain low. No physical correction is
selected because faction, persona, and backend effects are still entangled.

The diagnostic layer identified:

- Demis × Capability Rusher at four players;
- Demis × Capability Rusher at five players;
- Demis × greedy backend at three players; and
- one thin mixed-regime Demis interaction.

None entered the registered homogeneous rules gate, but all justify the
precommitted common-seed focal-faction diagnostic.

## AGI and negotiation

Across `47,520` player opportunities:

| Funnel stage | Players |
| --- | ---: |
| Met Capability, Customer, and Trust requirements | 21,908 |
| Needed external Power at the measured stage | 954 |
| Received a Power offer | 5,329 |
| Accepted the price | 5,329 |
| Became Grid-Ready | 156 |
| Had a legal declaration window | 12 |
| Declared | 12 |

Declarations occurred in zero three-player games, eight four-player games, and
four five-player games. Every four- and five-player declaration had a
counterfactually necessary supplier. Supplier competitive-finish rates were
`52.90%` at four and `66.08%` at five. Three-player Power sellers finished
competitively `73.97%` of the time, but no declaration reached a legal window.
This supports supplier viability while locating the main AGI collapse between
Grid-Ready and a legal declaration window. Human coercion, promises, and
kingmaking remain untested.

## Decision

Do not alter the physical rules from this matrix. Run the preregistered
common-seed faction swaps against the canonical promoted strategy ecology:

- Demis versus Mark with Capability Rusher;
- Demis versus Mark with Balanced Operator;
- Sam versus Mark with Power Broker; and
- Elon versus Mark with Infrastructure Compounder.

Use a separate fresh player-count scaling probe for Jensen after the
four-player faction diagnostic. Any candidate change must alter one authored
lever, use new common seeds, and rerun three, four, and five players.

## Surface audit

- Canonical rulebook: player range selected as three to five; no faction,
  action, resource, scoring, AGI, or infrastructure number changed from this
  report.
- Semantic graph and generated data: synchronized to the selected 3/4/5
  contract.
- Simulator and browser: reject two and six; accept three, four, and five.
- Unified matrix: four-player authority plus mandatory three/five coverage.
- Reference cards and component inventory: no component delta.
- Tests: supported-count acceptance, unsupported-count rejection, Audit
  scaling, and matrix-coverage gates added.
- Physical playtest protocol: four-player first, with required three/five
  regression sessions.
