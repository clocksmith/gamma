# Two-Compute Dossier study

**Date:** 2026-08-15  
**Status:** rejected  
**Game / rules:** `0.14.2` / `0.8.0-rc.3-test`  
**Source commit:** `51ec298c`  
**Preregistration:** `two-compute-dossier-v1`

## Hypothesis

Charging two Compute for every committed Dossier card might reduce frequent
AGI winner overrides while preserving the existing two-of-three evidence
routes and narrowing strategic dominance.

## Method

The clean-source unified matrix ran 5,990 matches. It paired the canonical
one-Compute cost against a two-Compute candidate on 2,960 common-seed pairs.
Coverage included three, four, and five players; fixed and variable Mandates;
all canonical rotating strategy windows; all factions and seats; and
homogeneous weighted, homogeneous greedy, and both alternating backend
regimes. The candidate changed only `agiComputePerCommit: 1 → 2`.

## Result

| Measure | Canonical | Two Compute |
| --- | ---: | ---: |
| AGI emergence, all counts | 26.89% | 7.91% |
| Three-player faction range | 16.34 pp | 16.67 pp |
| Four-player profile range | 23.54 pp | 21.81 pp |
| Five-player profile range | 22.00 pp | 19.71 pp |
| Four-player winning-path entropy | 0.675 | 0.668 |
| Five-player winning-path top share | 36.32% | 48.82% |

The candidate retained the AGI route near the registered target and modestly
narrowed profile spread. It nevertheless missed the four- and five-player
profile bounds, worsened the three-player faction range, and concentrated
winning paths. Four-player homogeneous Greedy Infrastructure remained at
`51.32%`; Greedy Power Broker and Trust Governor remained at `6.82%` and
`7.69%`. The cost does not repair the persistent strategy/action-validity
problem and is rejected.

## Artifacts

- Seed: `mandate-2038-two-compute-dossier-v1`
- Raw and archived report SHA-256:
  `ea4006a0ec87d686b24ca483e8aff50e82c32e3f6a7b17e320b8560619565797`
- Raw report:
  `2026-08-15-two-compute-dossier-v1.raw.json`
- Archive:
  `20260816T030240747Z-unified-matrix-audit-0-14-2-03ac2fbdec61-mandate-2038-two-compute-dossier-v1-5990x4-unified-matrix-cli.json`

## Surface audit

- Canonical rulebook, graph, data, browser, aids, and physical components: no
  change; the candidate was rejected.
- Simulator: existing one-lever overlay only; no new behavior.
- Tests and playtest protocol: no change required.

This is simulated falsification evidence, not a human playtest or a balance
claim. It specifically redirects the next investigation away from faction
starting resources and Dossier eligibility toward Default-game strategy and
Core Action viability.
