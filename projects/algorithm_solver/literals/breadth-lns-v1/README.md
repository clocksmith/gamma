# breadth-lns-v1: breadth-aware exact LNS objectives (board item 22)

[Freeze](FREEZE.md) `8b702e3c7`, [amendment 1](AMENDMENT-1.md) `42fb94036` (codex-approved), and an
[affinity note](NOTE-2026-10-23-affinity.md) `248492b73`. The run launched at about 20:49Z.

At 21:35Z, under the owner's new 0–15 core limit, the arms were moved without a restart from cores 26–31 (two per
arm) to cores 8, 9 and 10 (one each). Each arm used its full 5,400 s LNS budget (5,401–5,402 s), and all three
exited 0. [report.py](report.py) was committed at `b9dee5217` before validation opened. It replays each sealed
dictionary independently and re-measures all 400 programs. [Evidence](evidence/results.json) holds only
aggregates, IDs and hashes.

**Result: no arm is ready. nonregress protects breadth but gains almost nothing; relative fails to protect
breadth.**
- nonregress forbids any fit program from getting worse. It ends with 0 fit and 0 dev-val programs worse, but 16
  of its 18 repairs hit the 300 s solver limit without HiGHS *finding* a feasible point. These repairs are not
  infeasible: the removed entries stay among the candidates, so the current dictionary is always a feasible
  nonregression point. The repairs were cold-started, so this is a search limitation, not evidence against the
  constraint. The arm accepted one move (−14 fit selections).
- relative weights every program equally by its relative cost. It cut fit selections, but it made validation
  breadth worse than the plain objective did.
- unweighted, the item 11 objective, again gives the largest total gain with a concentrated cost, as in item 11.

| Arm | Moves (accepted) | Solver statuses | Fit selections | Fit better / worse | Dev-val actions | Median / p90 actions | p95 selections | Single-char | Package bytes | Dev-val better / same / worse vs pinned |
| --- | --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: | --- |
| pinned L-R-256 | – | – | 26,108 | – | 9,048 | 64.5 / 170 | 211 | 55.14% | 15,255 | – |
| unweighted | 27 (17) | 25 optimal, 2 time limit | 25,328 (−2.99%) | 106 / 116 | **8,814 (−2.59%)** | 66.0 / 161 | 182 | 54.67% | 15,719 | 34 / 23 / 43 |
| nonregress | 18 (1) | 2 optimal, 16 time limit | 26,094 (−0.05%) | 5 / 0 | 9,046 (−0.02%) | 64.5 / 170 | 211 | 55.13% | 15,254 | 1 / 99 / 0 |
| relative | 36 (23) | 35 optimal, 1 time limit | 25,717 (−1.50%) | 139 / 108 | 9,053 (+0.06%) | 67.5 / 164 | 217 | 56.63% | 16,010 | 33 / 16 / 51 |

- **Against unweighted on dev-val:** nonregress is better on 44, the same on 23 and worse on 33 programs.
  relative is better on 31, the same on 18 and worse on 51.
- **Relative.** Equal relative weights did not stop fit regressions: 108 fit programs got worse, against 116
  under unweighted. On dev-val, more programs got worse (51) than under any other arm, and the median and the
  single-character fraction both rose.
- **Unweighted vs item 11.** The unweighted dictionary differs from item 11's (`a61379bb…`) and ends 60 fit
  selections higher (25,328 vs 25,268 before polish). Its dev-val total is the same, 8,814 actions.

## Readiness against the pinned baseline (frozen bar)

| Arm | Failed checks |
| --- | --- |
| unweighted | at least 5% fewer actions; median lower; at least 60 better; at most 25 worse |
| nonregress | at least 5% fewer actions; median lower; p90 lower; at least 60 better |
| relative | at least 5% fewer actions; median lower; at least 60 better; at most 25 worse; fraction not higher |

All 400 programs decode in every arm, and the whole-solution audit is clean.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| B1 | unweighted within 1% of item 11's pre-polish 25,268 | true (25,328, +0.24%) |
| B2 | nonregress has 0 fit programs worse, and fewer dev-val programs worse than unweighted | true (0 fit; 0 vs 43 on dev-val) |
| B3 | relative has a lower dev-val median than unweighted | **false** (67.5 vs 66.0) |
| B4 | both breadth arms reduce dev-fit less than unweighted | true |
| B5 | no arm is ready | true |
| B6 | everything decodes, and the audit is clean | true |

## What this shows and does not show

- **Shows.** On R's dictionary, with this LNS budget and cold-started repairs, the per-program regression
  constraint keeps breadth but HiGHS rarely finds a feasible point within 300 s, so almost no gain is made. Equal
  relative weighting does not trade total gain for breadth. These two objective changes do not remove the
  concentration seen in item 11.
- **Does not show** that the nonregression constraint cannot yield gains. A warm start from the current
  dictionary, as in item 26's adapter, with the nonregression constraints included in the incumbent check, would
  always give the solver a feasible point. That would be a separately frozen comparison. A longer solver limit, a
  soft regression penalty or a quantile objective are also untested. These two objectives were tested only with
  this seed, budget and candidate rule.
- **Runtime change.** The arms moved from two cores each to one core each mid-run. scipy exposes no HiGHS
  thread option, so the effect on solver speed is unmeasured. The time-limit counts above include any slowdown.
- **Item 29**, which carries these objectives onto item 13, was frozen before this result and is unchanged by it.
