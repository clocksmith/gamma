# Calibrated strategy ecology holdout v2

**Date:** 2026-08-15  
**Status:** rejected; profile ecology remains outside bounds  
**Game / rules:** `0.14.4` / `0.8.0-rc.5-test`  
**Engine:** `0.16.3`  
**Source commit:** `2d9c78cf`  
**Preregistration:** `calibrated-strategy-ecology-holdout-v2`

## Method

The clean corrected-source holdout ran 11,928 matrix matches plus the
registered 70-match adversarial slice. It froze the same evolved Trust
Governor, curated Capacity Operator, and parity-calibrated AGI Candidate used
by v1. Physical rules, faction starts, and Core Actions remained canonical.
All supported player counts, fixed and variable Mandates, balanced rotations,
and four deterministic backend regimes were covered.

## Result

| Measure | 3 players | 4 players | 5 players | Bound |
| --- | ---: | ---: | ---: | ---: |
| Profile win-share range | 18.08 pp | 19.39 pp | 19.24 pp | at most 18 pp |
| Faction win-share range | 7.83 pp | 8.47 pp | 6.11 pp | at most 15 pp |
| Seat win-share range | 3.55 pp | 2.78 pp | 3.26 pp | at most 10 pp |
| Winning-path entropy | 0.673 | 0.630 | 0.586 | at least 0.600 |
| Winning-path top share | 37.59% | 36.73% | 38.03% | at most 55% |
| AGI emergence | 26.69% | 32.18% | 38.03% | diagnostic |

No marginal, pairwise, or diagnostic dominance cell survived the corrected
winner-aware gate. This confirms that v1's 89–91% raw-Mandate head-to-head
signal was a measurement artifact.

The package still fails. AGI Candidate was strongest at every count, winning
`42.33%`, `36.46%`, and `32.97%` of its appearances. Trust Governor fell to
`24.25%`, `17.07%`, and `13.73%`. Profile spread failed at every count, while
five-player AGI declaration became the largest winning path and reduced path
entropy below the bound.

Faction and seat bounds passed everywhere. The result again supplies no
evidence for changing starting resources.

## Identity checks

- Trust Governor selected Influence `1.72` times per appearance, below
  Research at `3.85`, reached Trust 4 in approximately `94.3%` of appearances,
  and averaged `17.16` Mandate.
- Capacity Operator selected Build `2.22` times per appearance; Research plus
  Deploy reached `6.65`, and mean Mandate was `17.26`.
- AGI Candidate supplied `2,122` of `3,849` AGI-declaration winner credits
  (`55.13%`), the largest profile contribution, averaged `14.24` Mandate, and
  retained Dossier as its highest Program weight.

All identities passed. The profile package remains unpromotable.

## Decision

- Do not promote the three profiles.
- Do not change faction starts or Core Actions. Their faction/seat evidence is
  bounded, and the repeated defect tracks AGI/Trust strategy ecology.
- Do not immediately promote two Compute per Dossier commitment. The earlier
  isolated study reduced AGI but concentrated other winning paths and failed
  profile bounds.
- Correct the strategy optimizer's opponent coverage before nominating a
  physical rule. The parity-calibrated AGI candidate trained against one fixed
  opponent window; it was never calibrated against Trust Governor or Capacity
  Operator, even though the holdout rotated both. A calibration target cannot
  generalize to an ecology it did not sample.

## Artifacts

- Seed: `mandate-2038-calibrated-strategy-ecology-holdout-v2`
- Raw and archived report SHA-256:
  `b31861a6bc806a72d92f7a7d343e14500e16ba3f140056fb102c116e304daff7`
- Raw report: `2026-08-15-calibrated-strategy-ecology-holdout-v2.raw.json`
- Archive:
  `20260816T060359765Z-unified-matrix-audit-0-14-4-03ac2fbdec61-mandate-2038-calibrated-strategy-ecology-holdout-v2-11998x4-unified-matrix-cli.json`

This is deterministic simulation evidence, not proof of human balance, fun,
negotiation quality, or teachability.
