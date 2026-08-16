# Three-evidence Dossier study

**Date:** 2026-08-15  
**Status:** rejected  
**Game / rules:** `0.14.2` / `0.8.0-rc.3-test`  
**Source commit:** `b585f534`  
**Preregistration:** `three-evidence-dossier-v1`

## Hypothesis

Requiring Benchmark, Deployment, and Authority support might reduce frequent
Dossier winner overrides and narrow strategic dominance without removing the
AGI endgame.

## Method

The clean-source unified matrix ran 5,990 matches. It paired canonical
two-of-three evidence against a three-of-three candidate on 2,960 common-seed
pairs. Coverage included three, four, and five players; fixed and variable
Mandates; all canonical rotating strategy windows; all factions and seats; and
homogeneous weighted, homogeneous greedy, and both alternating backend
regimes. The candidate changed only
`agiMinimumSupportedEvidenceClaims: 2 → 3`.

## Result

| Measure | Canonical | Three evidence |
| --- | ---: | ---: |
| AGI emergence, all counts | 27.30% | 0.24% |
| Four-player profile range | 22.59 pp | 18.85 pp |
| Five-player profile range | 20.78 pp | 25.74 pp |
| Five-player winning-path entropy | 0.666 | 0.579 |
| Faction range, all counts | 8.06 pp | 11.50 pp |

The candidate nearly deleted the AGI path, still missed the authoritative
four-player profile bound, worsened five-player profile spread, and failed the
five-player winning-path entropy floor. Five-player Greedy Infrastructure
remained the report's diagnostic dominance cell. The candidate is rejected.

## Artifacts

- Seed: `mandate-2038-three-evidence-dossier-v1`
- Raw and archived report SHA-256:
  `a0ad960f9a7a2ab0fe303c89d77ebd362d4e96c56deccec4cedc50824990bf18`
- Raw report:
  `2026-08-15-three-evidence-dossier-v1.raw.json`
- Archive:
  `20260816T024918166Z-unified-matrix-audit-0-14-2-03ac2fbdec61-mandate-2038-three-evidence-dossier-v1-5990x4-unified-matrix-cli.json`

## Surface audit

- Canonical rulebook, graph, data, browser, aids, and physical components: no
  change; the candidate was rejected.
- Simulator: existing one-lever overlay only; no new behavior.
- Tests and playtest protocol: no change required.

This is simulated falsification evidence, not a human playtest or a balance
claim.
