# Full-ecology AGI holdout v1

**Date:** 2026-08-15  
**Status:** profile package rejected; exact-ecology training boundary required  
**Game / rules / engine:** `0.14.5` / `0.8.0-rc.6-test` / `0.16.4`  
**Source commit:** `fda4f9585c9d969d2082ce9f3c0c4fd985595418`  
**Source state:** clean

## Question

Does the frozen full-ecology AGI Candidate remove the remaining strategy and
winning-path defects when combined with the previously frozen Trust Governor
and Capacity Operator under unchanged physical rules?

## Method

[`full-ecology-agi-holdout-v1.json`](preregistrations/full-ecology-agi-holdout-v1.json)
froze one AGI profile substitution, fresh seeds, all supported player counts,
fixed and variable Mandates, four deterministic backend regimes, balanced
faction and seat rotation, 11,928 matrix matches, and seventy adversarial
matches. The report followed winner-aware placement and used no physical-rules
overlay.

## Verdict

The package is outside the provisional bounds. The AGI candidate is not
promoted.

The automated core gate had one failure:

| Check | Value | Bound |
| --- | ---: | ---: |
| Five-player winning-path entropy | 0.5911 | at least 0.6000 |

The preregistered diagnostic gate also failed. Three-player Infrastructure
Compounder under the greedy backend won `60.76%` of 864 appearances; its
posterior interval was `56.86%–63.33%`. The matrix reported no marginal,
pairwise, or adversarial dominance, but this exact strategy/backend cell was
declared unacceptable before the run.

## Supported-count results

| Players | Faction range | Seat range | Profile range | AGI emergence | Path entropy |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 8.39 pp | 1.07 pp | 17.79 pp | 20.15% | 0.6337 |
| 4 | 7.35 pp | 1.15 pp | 14.52 pp | 25.18% | 0.6165 |
| 5 | 8.08 pp | 4.98 pp | 13.02 pp | 28.26% | 0.5911 |

Faction, seat, and profile ranges all passed. Starting resources and turn
order are therefore not implicated by this holdout.

The AGI candidate reduced its prior corrected-holdout shares from
`42.33% / 36.46% / 32.97%` to `38.38% / 29.81% / 23.33%` at three, four, and
five players. That is a material reduction, but the three-player rate remains
inside the preregistered prior-failure range and cannot support promotion.

## Identity checks

- Trust Governor averaged `1.73` Influence selections per appearance, kept
  Research as its largest Core Action, reached Trust four in approximately
  `93.9%` of appearances, and retained mean Mandate above sixteen at every
  player count.
- Capacity Operator averaged `2.23` Builds per appearance, averaged `6.68`
  Research-plus-Deploy selections, and retained mean Mandate above seventeen.
- AGI Candidate supplied `1,141 / 2,925` AGI winner credits (`39.01%`), more
  than any other profile, and retained mean Mandate from `15.14` to `15.52`.
  Dossier remained its largest Program weight.

These checks show that the failure is not an identity collapse. Infrastructure
Compounder is the named residual strategy/backend defect, while concentrated
five-player research/adoption and AGI paths remain the diversity defect.

## Training-boundary finding

The corrected optimizer covered every circular opponent-ID window, but its
runtime loaded non-target opponents from canonical profile data. It could not
inject the exact frozen Trust Governor and Capacity Operator artifacts used by
this holdout. Therefore the training label “full ecology” was correct for IDs
but not exact for opponent policy versions. That mismatch does not invalidate
this held-out result; it prevents another profile-training claim until exact
opponent artifacts are accepted, fingerprinted, and executed by the optimizer.

## Artifacts

- Raw report: `2026-08-15-full-ecology-agi-holdout-v1.raw.json`
- Raw SHA-256:
  `cd4d93cb00db515ab4f99903e8bd5a478b076b30b0014801cc405ec1d0b00f30`
- Archive:
  `20260816T071030263Z-unified-matrix-audit-0-14-5-03ac2fbdec61-mandate-2038-full-ecology-agi-holdout-v1-11998x4-unified-matrix-cli.json`

## Decision boundary

Do not change faction starts, Core Actions, or Dossier requirements from this
result. First make strategy evolution execute and fingerprint the exact frozen
opponent ecology. Then preregister one Infrastructure Compounder intervention;
do not repeat AGI or Trust training adaptively. Any resulting package still
requires a fresh unified holdout and explicit human approval.

Simulation cannot establish human counterplay, negotiation quality, fun,
teachability, duration, or physical handling.
