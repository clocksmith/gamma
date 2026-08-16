# Exact-ecology Infrastructure training v1

**Date:** 2026-08-15  
**Status:** Infrastructure Compounder nominated for unified holdout  
**Game / rules / engine:** `0.14.6` / `0.8.0-rc.7-test` / `0.16.5`  
**Source commit:** `315f09f73af33803980291e7f00c4bf8b2940ced`  
**Source state:** clean

## Question

Can Infrastructure Compounder remove its registered three-player greedy
dominance and approach neutral share across all supported counts when trained
against the exact frozen Trust, Capacity, and AGI artifacts?

## Frozen method

[`exact-ecology-infrastructure-training-v1.json`](preregistrations/exact-ecology-infrastructure-training-v1.json)
registered one five-generation, six-candidate job. Each candidate played twelve
matches from every focal seat at three, four, and five players. Matches were
divided evenly across all six circular opponent windows. The optimizer loaded
the exact opponent artifacts and retained their source paths, SHA-256 digests,
complete profiles, and strategy fingerprints in the raw report.

The job evaluated 4,320 matches. Candidate ordering minimized the largest miss
from `1 / player count`, then mean miss, then ordinary fitness. Mutation could
change action, decision, and negotiation weights. It could not change setup,
factions, Core Actions, legal actions, scoring, Dossier requirements, strategy
rules, or physical components.

## Result

| Measure | Authored baseline | Training nominee |
| --- | ---: | ---: |
| Largest supported-count miss | 28.33 pp | 4.17 pp |
| Mean supported-count miss | 27.73 pp | 1.94 pp |
| Three-player win share | 61.11% | 33.33% |
| Four-player win share | 52.08% | 20.83% |
| Five-player win share | 48.33% | 18.33% |
| Three-player mean Mandate | 19.69 | 17.58 |
| Four-player mean Mandate | 21.08 | 17.54 |
| Five-player mean Mandate | 20.28 | 17.57 |

The nominee passes the preregistered training floor. It improves the authored
baseline's largest neutral-share miss, keeps mean Mandate above sixteen at
every supported count, retains the authored Generator and two-Facility
transition rules, and raises Build from `3.800` to `6.530`. It advances only as
a frozen candidate for a fresh unified holdout.

## Frozen ecology

- Trust Governor source SHA-256:
  `a2a26d027b06d85c75178e6c6c468aa6ad3c5ae32b82292e3d84caeca173a462`
- Capacity Operator proposal SHA-256:
  `186bb26d4eaf01fedbb03bb3e7e0ad89a4aa6e544dcf6737142be70a7672b6f7`
- AGI Candidate proposal SHA-256:
  `3bca97e398eab032ae5befe322f266f67b21119ed68848f2cc2f4661016c94a6`

## Artifacts

- Raw report: `2026-08-15-exact-ecology-infrastructure-training-v1.raw.json`
- Raw SHA-256:
  `36cae447340ca34787781563563b219d13b44232bdcbe434557d7a36ef189c07`
- Infrastructure proposal:
  `proposals/exact-ecology-infrastructure-candidate-v1.json`
- Proposal SHA-256:
  `af0cefe1680c20469430dc94cfa78572ac6150d1e9e7234708a468e6872e3566`

## Decision boundary

This training result nominates one Infrastructure policy artifact. It does not
promote a profile, prove package balance, or justify changing starting
resources or Core Actions. The candidate must pass a fresh-seed unified holdout
with the exact frozen ecology. That holdout must remove the registered
three-player greedy dominance, retain Infrastructure's Build and Mandate
identity, and restore five-player winning-path entropy to at least `0.60`.

Simulation cannot establish human counterplay, negotiation quality, fun,
teachability, duration, or physical handling.
