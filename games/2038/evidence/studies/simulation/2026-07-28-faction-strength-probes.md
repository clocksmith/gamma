# Faction strength probes

Date: 2026-07-28  
Evidence label: preregistered one-lever simulation matrix  
Verdict: reject both candidates; directly doubling Scientific Method's price
and Industrial Velocity's discount changes resources but not faction outcomes

## Identity

- Raw local report:
  `20260728T025004207Z-unified-matrix-audit-0-8-1-7b491dc09736-m3t4-faction-strength-probes-v1-fresh-20260728-17998x4-unified-matrix-cli.json`
- Report SHA-256:
  `ff011c8e3119913dc1d7847f7d0762e7b39d5052bc67f7cac2d74a12cc0aee7b`
- Source commit:
  `d45acd7ce3ac48a46e88daeada07b1cfc1ad3ad7`
- Source dirty: `false`
- Executable: `0.8.1`
- Engine: `selected-rules` `0.10.1`
- Coverage: `three-to-five-grid-ready-v1`
- Physical candidate: `0.5.0-rc.2-test`
- Preregistration: `faction-strength-probes-v1`
- Root seed: `m3t4-faction-strength-probes-v1-fresh-20260728`
- Matrix matches: `17,928`
- Bounded adversarial matches: `70`
- Matches per arm: `5,976`
- Common-seed pairs per candidate: `5,976`
- LLM calls: `0`

The three independent arms were canonical, Scientific Method costing two
Runway, and Industrial Velocity discounting two Runway. The frame covered
three, four, and five players; fixed and variable Mandates; all canonical
personas in rotating windows; balanced faction/seat rotation; and homogeneous
and alternating weighted/greedy backends.

## Validity

- Three-player matches: `6,324`
- Four-player matches: `5,928`
- Five-player matches: `5,676`
- Integrity violations: `0`
- Policy fallbacks: `0`
- Forced-no-op rate: `0.3795%`
- Registered homogeneous dominance cells: `0`
- Registered pairwise dominance cells: `0`
- Diagnostic dominance cells: `0`
- Credible meta cycles: `0`
- Matrix status: `inconclusive_precision_not_reached`
- Maximum core confidence-sequence half-width: `0.2581`

The clean execution and exact common-seed pairing validate the direction and
small realized size of the candidate effects. The registered global precision
target was not reached, so the matrix is not a balance certification.

## Scientific Method costs two Runway

Across `4,004` paired Demis appearances:

- win-share delta: `-0.608` percentage points;
- mean-score delta: `-0.086`;
- bounded multiplicity-adjusted interval: `[-5.840, +4.624]` percentage
  points.

Raw Demis win rates changed:

| Players | Canonical | Candidate | Delta |
| --- | ---: | ---: | ---: |
| 3 | 49.41% | 49.28% | -0.14 pp |
| 4 | 36.68% | 35.93% | -0.75 pp |
| 5 | 26.34% | 25.51% | -0.82 pp |

The price reduced Scientific Method uses from `2,430` to `2,263` and increased
Runway paid from `2,430` to `4,526`, yet Capability preserved only fell from
`6,012` to `5,560`. The ability remains worth using, and the additional
economic tax barely changes standings.

## Industrial Velocity discounts two Runway

Across `4,116` paired Elon appearances:

- win-share delta: `-0.121` percentage points;
- mean-score delta: `+0.027`;
- bounded multiplicity-adjusted interval: `[-5.282, +5.039]` percentage
  points.

Raw Elon win rates changed:

| Players | Canonical | Candidate | Delta |
| --- | ---: | ---: | ---: |
| 3 | 21.49% | 21.04% | -0.45 pp |
| 4 | 17.24% | 17.39% | +0.14 pp |
| 5 | 12.24% | 12.11% | -0.12 pp |

The candidate increased recorded Runway savings from `5,800` to `10,736`
without improving outcomes. Extra unspent Runway is not the faction's binding
constraint, so a larger discount is the wrong balance instrument.

## Canonical context

Canonical partially pooled faction win rates remained:

| Faction | 3 players | 4 players | 5 players |
| --- | ---: | ---: | ---: |
| Sam Altman | 23.04% | 15.74% | 11.95% |
| Mark Zuckerberg | 31.10% | 22.89% | 19.54% |
| Demis Hassabis | 48.98% | 36.50% | 26.32% |
| Elon Musk | 21.55% | 17.36% | 12.40% |
| Dario Amodei | 37.01% | 28.36% | 23.25% |
| Jensen Huang | 36.84% | 29.19% | 27.09% |

These are conditional faction-appearance rates and do not sum to 100%.

## Decision

Reject both candidates and leave the physical rules unchanged. Do not make
Scientific Method more expensive or Industrial Velocity cheaper in a later
revision without materially different evidence.

The next candidate must alter conversion into victory-relevant progress, not
merely add or subtract a resource the deterministic policies already fail to
convert. Any next probe remains independently preregistered and requires a new
seed bank.

## Surface audit

- Canonical rulebook: no change.
- Semantic graph and generated data: no rule change.
- Simulator: retains both inactive overlay fields for exact reproduction.
- Browser prototype: canonical values unchanged.
- Reference cards and player aids: no change.
- Tests: overlay isolation and canonical defaults remain covered.
- Playtest documentation: no change.
- Immutable release: `0.8.1` and `0.5.0-rc.2-test` identify the clean probe
  source; neither candidate is canonical.
- Physical components and artwork: no change.

