# Default strategy ecology confirmation

**Date:** 2026-08-15  
**Status:** rejected; credible five-player matchup dominance  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `57e8ef0b`  
**Preregistration:** `default-strategy-ecology-confirmation-v1`

## Method

The clean-source confirmation ran 11,998 matches on fresh seeds with the
frozen Trust Governor and Capacity Operator candidates. Physical rules and
faction starts were unchanged. The matrix covered three, four, and five
players; fixed and variable Mandates; balanced faction, seat, and profile
rotation; homogeneous weighted and greedy backends; and both alternating
backend regimes.

## Result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 15.16 pp | 17.94 pp | 14.78 pp | at most 18 pp |
| Faction win-share range | 7.22 pp | 8.79 pp | 8.68 pp | at most 15 pp |
| Seat win-share range | 1.65 pp | 2.46 pp | 2.55 pp | at most 10 pp |
| Winning-path entropy | 0.678 | 0.665 | 0.597 | at least 0.600 |
| Winning-path top share | 40.93% | 39.69% | 41.19% | at most 55% |
| AGI emergence | 21.20% | 27.10% | 30.37% | diagnostic |

The original four-player profile-range question passed with a `17.94` pp
range. Faction and seat ranges also passed at every supported count. The
confirmation nevertheless rejects the complete ecology for two independent
reasons:

1. Five-player winning-path entropy was `0.5973`, below the `0.6000` floor.
2. In five-player homogeneous-greedy games, Infrastructure Compounder beat AGI
   Candidate head to head at an estimated `87.50%` over `424` exposures. Its
   multiplicity-safe confidence-sequence lower bound was `70.32%`, above the
   `70%` dominance threshold.

Four-player Infrastructure Compounder with the greedy backend was also a
diagnostic concern at `52.53%` win share over `1,128` exposures, but it did not
cross the core confidence gate. No faction, seat, or starting-state dominance
was detected.

## Candidate identity

Trust Governor selected Influence `11,494` times in `6,704` appearances
(`1.71` per appearance), below Research at `3.86` per appearance. It reached
Trust 4 in approximately `94.4%` of appearances, inferred from threshold
Mandate awards, and averaged `16.94` Mandate.

Capacity Operator selected Build `15,323` times in `6,816` appearances
(`2.25` per appearance). Research plus Deploy totaled `45,538` selections
(`6.68` per appearance), and mean Mandate was `17.13`.

Both candidates passed their behavior-identity checks. They remain frozen
candidates, not canonical profiles, because the complete ecology failed.

## Decision

- Do not alter faction starting resources. The enlarged confirmation makes
  that intervention less defensible, not more.
- Do not buff or rewrite Influence from this study. Trust's behavior and
  aggregate profile range passed; the credible failure is specifically
  Infrastructure Compounder versus AGI Candidate at five players.
- Retrain or correct the stale AGI Candidate policy against the current
  evidence-aware Dossier semantics, then run a fresh all-count holdout with
  the frozen Trust and Capacity candidates.
- Do not raise Dossier commitment cost yet. That would directly weaken the
  already dominated AGI Candidate and risks worsening the measured matchup.

## Artifacts

- Seed: `mandate-2038-default-strategy-ecology-confirmation-v1`
- Raw and archived report SHA-256:
  `9b3d2d5dc8c1f735a0c7e6478c0820c183ba6e2b38835d5fbc6c878ff508b260`
- Raw report:
  `2026-08-15-default-strategy-ecology-confirmation-v1.raw.json`
- Archive:
  `20260816T040936338Z-unified-matrix-audit-0-14-3-03ac2fbdec61-mandate-2038-default-strategy-ecology-confirmation-v1-11998x4-unified-matrix-cli.json`

## Limits

This rejects one deterministic strategy ecology. It does not prove that
Infrastructure is dominant for human players, that AGI is intrinsically weak,
or that the physical game is balanced. Human negotiation, bluffing,
teachability, and enjoyment still require rotated physical playtests.
