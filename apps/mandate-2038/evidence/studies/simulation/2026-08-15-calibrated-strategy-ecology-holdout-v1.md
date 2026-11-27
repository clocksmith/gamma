# Calibrated strategy ecology holdout v1

**Date:** 2026-08-15  
**Status:** invalidated for promotion; winner-placement measurement defect  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `4febc294`  
**Preregistration:** `calibrated-strategy-ecology-holdout-v1`

## Method

The clean-source holdout ran 11,928 matrix matches plus the registered
70-match adversarial slice. It froze the evolved Trust Governor, curated
Capacity Operator, and parity-calibrated AGI Candidate while retaining all
physical rules and faction starts. Coverage included every supported player
count, fixed and variable Mandates, balanced faction/seat/profile rotation,
and all four deterministic backend regimes.

## Recorded result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 19.36 pp | 17.67 pp | 19.12 pp | at most 18 pp |
| Faction win-share range | 9.05 pp | 6.81 pp | 7.47 pp | at most 15 pp |
| Seat win-share range | 1.60 pp | 1.80 pp | 2.02 pp | at most 10 pp |
| Winning-path entropy | 0.658 | 0.628 | 0.587 | at least 0.600 |
| Winning-path top share | 37.93% | 37.22% | 38.28% | at most 55% |
| AGI emergence | 26.24% | 32.52% | 38.28% | diagnostic |

Faction and seat bounds passed at every count. Starting resources remain
unimplicated. The profile range failed at three and five players, and
five-player winning-path entropy failed. AGI Candidate remained the strongest
mixed-roster profile at `44.04%`, `35.24%`, and `32.56%` win share.

## Invalid head-to-head verdict

The report classified Capability Rusher over AGI Candidate at `89.00%` and
Infrastructure Compounder over AGI Candidate at `91.02%` in five-player
homogeneous-greedy cells. Those cells compared raw Mandate score rather than
the authoritative `winnerSeats`. A successful AGI declaration can legally
replace the Mandate winner, so the evaluator counted a lower-Mandate AGI
winner as losing every pairwise comparison against higher-Mandate
non-winners.

The same defect affected reported mean rank, supplier top-half status,
rule-comparison rank deltas, and Monte Carlo matchup placement. The report's
`credible_dominance_detected` status is therefore invalid. Profile win share,
faction win share, seat win share, path diversity, and AGI emergence use
authoritative winner credit and retain descriptive value, but they cannot
promote this package.

## Identity checks

- Trust Governor selected Influence `1.71` times per appearance, below
  Research at `3.85`, reached Trust 4 in approximately `94.2%` of appearances,
  and averaged `17.18` Mandate.
- Capacity Operator selected Build `2.23` times per appearance; Research plus
  Deploy reached `6.65`, and mean Mandate was `17.24`.
- AGI Candidate supplied `2,121` of `3,855` AGI-declaration winner credits
  (`55.02%`), the largest profile contribution, averaged `14.17` Mandate, and
  retained Dossier as its highest Program weight.

All identity checks passed. They do not override the failed mixed-roster
profile and path bounds.

## Decision

- Do not promote the profile package from this report.
- Correct every analysis surface to rank the authoritative institutional
  winner first while retaining Mandate as a separate score measure.
- Rerun the frozen preregistered matrix from clean corrected source.
- Do not change faction starts, Core Actions, or Dossier cost from this report.
  The false head-to-head result must be removed before a physical mechanism is
  nominated.

## Artifacts

- Seed: `mandate-2038-calibrated-strategy-ecology-holdout-v1`
- Raw and archived report SHA-256:
  `0a8be7f333edcb4c401afdbbc760d70d925ae7ee458ca1931f5f21b1ba2e8089`
- Raw report: `2026-08-15-calibrated-strategy-ecology-holdout-v1.raw.json`
- Archive:
  `20260816T052855339Z-unified-matrix-audit-0-14-3-03ac2fbdec61-mandate-2038-calibrated-strategy-ecology-holdout-v1-11998x4-unified-matrix-cli.json`

This is deterministic simulation evidence, not proof of human balance, fun,
negotiation quality, or teachability.
