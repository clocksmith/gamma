# Three-profile ecology holdout

**Date:** 2026-08-15  
**Status:** rejected; AGI Candidate overfit  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `d61834f4`  
**Preregistration:** `three-profile-ecology-holdout-v1`

## Method

The clean-source holdout ran 11,998 matches on untouched seeds with frozen
Trust Governor, Capacity Operator, and corrected AGI Candidate profiles.
Physical rules and faction starts remained canonical. Coverage included every
supported player count, fixed and variable Mandates, balanced faction/seat/
profile rotation, all four deterministic backend regimes, and the adversarial
slice.

## Result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 26.50 pp | 21.47 pp | 19.42 pp | at most 18 pp |
| Faction win-share range | 7.06 pp | 9.12 pp | 8.48 pp | at most 15 pp |
| Seat win-share range | 0.15 pp | 1.31 pp | 1.37 pp | at most 10 pp |
| Winning-path entropy | 0.585 | 0.597 | 0.603 | at least 0.600 |
| Winning-path top share | 47.71% | 46.12% | 44.83% | at most 55% |
| AGI emergence | 18.81% | 22.59% | 26.61% | diagnostic |

The previous five-player greedy Infrastructure Compounder–AGI Candidate
dominance disappeared: no marginal or pairwise dominance survived the
registered confidence gates. The correction nevertheless overshot. AGI
Candidate won `49.38%`, `38.53%`, and `32.73%` at three, four, and five players
respectively. Profile spread failed at every count, and winning-path entropy
failed at three and four players.

Faction and seat ranges passed everywhere. The result supplies no evidence
for changing faction starts.

## Identity checks

- AGI Candidate supplied `1,011` of `2,702` AGI-declaration winner credits
  (`37.42%`), the largest profile contribution, and averaged `17.93` Mandate.
  Dossier remained its highest Program weight. Its identity passed, but its
  strength did not.
- Trust Governor selected Influence `1.70` times per appearance, below
  Research at `3.85`, reached Trust 4 in approximately `94.2%` of appearances,
  and averaged `17.24` Mandate.
- Capacity Operator selected Build `2.21` times per appearance; Research plus
  Deploy reached `6.73` per appearance, and mean Mandate was `17.41`.

All three identity checks passed. The package is still rejected because
identity cannot substitute for balance.

## Decision

- Do not promote any of the three profiles as a package.
- Do not change starting resources or Core Actions. The failure follows the
  newly optimized AGI policy while faction and seat effects remain bounded.
- Replace win-maximizing AGI training with a preregistered calibration target.
  Five-player training should seek the neutral `1/5` profile share rather than
  maximize victory, while preserving AGI identity. A new all-count holdout is
  mandatory.
- Do not change Dossier cost from this result. The policy correction changed
  AGI emergence and profile strength substantially under identical physical
  rules, demonstrating that policy quality remains a live confounder.

## Artifacts

- Seed: `mandate-2038-three-profile-ecology-holdout-v1`
- Raw and archived report SHA-256:
  `e2da7547f81829b3fa0181ae7baf7f14be9c4b4fefe59421dcfe1fb3fe08b271`
- Raw report: `2026-08-15-three-profile-ecology-holdout-v1.raw.json`
- Archive:
  `20260816T045527894Z-unified-matrix-audit-0-14-3-03ac2fbdec61-mandate-2038-three-profile-ecology-holdout-v1-11998x4-unified-matrix-cli.json`

This is deterministic simulation evidence, not proof of human balance or fun.
