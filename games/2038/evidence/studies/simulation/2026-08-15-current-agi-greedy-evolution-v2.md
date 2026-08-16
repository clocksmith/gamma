# AGI Candidate greedy evolution v2

**Date:** 2026-08-15  
**Status:** training candidate; requires fresh holdout  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `1cf36f8d`  
**Backend / players:** greedy / five

## Purpose

Train AGI Candidate against the exact five-player greedy condition in which
Infrastructure Compounder produced credible head-to-head dominance. The
optimizer included the corrected high-weight mutation contract, so the
authored Dossier weight of `60` was not silently clamped to `20`.

## Training result

The search evaluated six generations of eight candidates, with 24 games per
seat. The final incumbent reached `27.08%` mean training win share on its final
generation's common seeds. Generation champions ranged from `19.44%` to
`27.08%`; these changing training seeds are not a held-out comparison.

The frozen candidate preserves AGI identity while changing its preparation:

| Weight | Canonical | Candidate |
| --- | ---: | ---: |
| Dossier | 60.000 | 38.396 |
| Research | 9.000 | 9.786 |
| Build | 10.000 | 4.496 |
| Deploy | 8.000 | 5.327 |
| Open Weights | 6.000 | 9.031 |
| Dossier Commit decision | 20.000 | 9.375 |

Dossier remains the candidate's largest Program priority. The policy reduces
unconditional construction, increases research, and gives evidence-aware
Commit/Hedge assessment more influence instead of forcing Commit through a
weight of `20`.

## Artifact

- Seed: `mandate-2038-current-agi-greedy-evolution-v2`
- Raw report: `2026-08-15-current-agi-greedy-evolution-v2.raw.json`
- SHA-256:
  `11d8f636587d3692d3210835ec0cca9c0ae7d2d1f4b972d341172f338ae83285`

This candidate may advance only if a fresh three-, four-, and five-player
holdout removes the measured matchup dominance, preserves strategy identity,
and passes every registered balance and diversity bound.
