# AGI Candidate greedy calibration v3

**Date:** 2026-08-15  
**Status:** calibrated training candidate; requires fresh holdout  
**Game / rules:** `0.14.3` / `0.8.0-rc.4-test`  
**Source commit:** `bd4f5405`  
**Backend / players / target:** greedy / five / `20%`

## Purpose

Calibrate AGI Candidate to the neutral five-player profile share instead of
maximizing wins. The prior win-maximizing candidate removed its original
matchup weakness but dominated every supported count.

## Training result

The search evaluated six generations of eight candidates, with 24 games per
seat. Generation champions measured `15.83%`, `17.50%`, `20.00%`, `16.67%`,
`20.00%`, and `20.83%` on their generation-specific common seeds. The frozen
incumbent came from generation five and reevaluated at `20.83%` in generation
six.

The candidate preserves its distinctive Dossier plan:

| Weight | Canonical | Candidate |
| --- | ---: | ---: |
| Dossier | 60.000 | 52.931 |
| Agent Swarm | 7.000 | 14.505 |
| Build | 10.000 | 11.190 |
| Research | 9.000 | 7.692 |
| Deploy | 8.000 | 2.663 |
| Dossier Commit decision | 20.000 | 18.327 |

Dossier remains the largest Program weight. The candidate emphasizes the
Facility/evidence base and a late Agent Swarm while reducing routine Deploy
priority. Whether that behavior remains fair and intelligible is a holdout
question, not a training conclusion.

## Artifact

- Seed: `mandate-2038-current-agi-greedy-calibration-v3`
- Raw report: `2026-08-15-current-agi-greedy-calibration-v3.raw.json`
- SHA-256:
  `ba674a7febbc18eeda6b18e1cae5cda03ecaf0ce8f218af0b67cf668807cb75c`

This is training evidence only.
