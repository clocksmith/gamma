# warm-nonregress-v1: warm versus cold nonregression repair (board item 37)

[Freeze](FREEZE.md) `5d7273d84`, [amendment 1](AMENDMENT-1.md) `fd8958a2b` and `2d2aa36a0` (codex-reviewed). The run
started at 22:49Z on cores 8 and 9, one per arm. Each arm used its 3,600 s LNS budget, and both exited 0.

[evidence.py](evidence.py) first verifies the pinned contract. It replays each sealed dictionary over all 400 programs,
and rebuilds every reported counter from the replay and from the retained `moves.jsonl` before evaluating anything.
Qualification is reused by exact source hash from item 13's receipt; all 400 were asserted.
[Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

## Result

**Both arms are frozen-rule successors of item 13, and they are the same successor.** Both protect breadth: 0 programs
get worse on fit or on dev-val. Neither is the new current best; item 24 remains.

| | Item 13 seed | warm | cold |
| --- | ---: | ---: | ---: |
| Moves / accepted | – | 16 / 4 | 16 / 4 |
| Solver: optimal / time limit | – | 12 / 4 | 12 / 4 |
| Feasible points returned | – | 16 / 16 | 12 / 16 |
| Fit selections | 24,750 | 24,512 (−0.96%) | 24,512 (−0.96%) |
| Fit programs better / worse | – | 57 / 0 | 57 / 0 |
| **Dev-val actions** | 8,504 | **8,377 (−1.49%)** | **8,377 (−1.49%)** |
| Median / p90 actions | 62.5 / 155 | **62.0** / 155 | **62.0** / 155 |
| Median / p95 selections | 61.5 / 199 | 61.0 / 199 | 61.0 / 199 |
| Within 32 / 96 selections | 17 / 70 | 17 / 71 | 17 / 71 |
| Single-character fraction | 49.89% | 49.78% | 49.78% |
| Package bytes | 14,724 | 14,725 | 14,725 |
| Dev-val vs item 13: better / same / worse | – | **26 / 74 / 0** | **26 / 74 / 0** |
| Dev-val vs R: better / same / worse | 75 / 21 / 4 | 77 / 20 / 3 | 77 / 20 / 3 |
| Dev-val vs item 24: better / same / worse | 14 / 53 / 33 | 27 / 46 / 27 | 27 / 46 / 27 |

- **Same trajectory.** The two arms accepted the same 4 moves, at moves 4, 6, 7 and 11, and ended on the identical
  dictionary (`3a302539…`). Warm against cold is the same on all 300 fit and all 100 dev-val programs.
- **Selection.** The frozen ranking (actions, then package bytes, then arm name) selects **cold** on the name tie.
- **Against item 24,** both arms fail strictly fewer actions (8,377 vs 8,336), fraction no higher (49.78% vs 49.60%),
  and at most 25 worse (27 worse). So M1-GAP's current-best row is unchanged.

## What the warm start did, and what actually unblocked the repair

- **The warm start changed only the time-limited calls.** On the 4 calls that hit the time limit, warm returned the
  supplied incumbent and cold returned nothing. On these 4 calls neither arm found an improvement, so neither
  trajectory changed.
- **The stall in items 22 and 29 was not caused by a missing start.** Item 29's nonregress arm and this run's cold arm
  share the same seed, `random.Random(8)` and candidate rule. Their first snapshot is therefore the same (4,019
  candidates).
  - Item 29 used SciPy's `milp`. It hit the 300 s limit with no feasible point on its first three snapshots, and on
    all 18 of its moves.
  - This cold arm uses item 26's direct-HiGHS model, with `threads=1`, `random_seed=8` and cap rows. It solved the
    first two of those snapshots to optimality in 156 s and 168 s.

  The difference is the solver interface and configuration. This run cannot say which part matters: threads, seed,
  presolve or model-build details. It is not the warm start.
- **Time-limit overruns.** Four calls per arm ended at the time limit, and some ran far past the 300 s limit:
  - cold move 2: 804 s;
  - warm moves 2 and 5: 521 s and 507 s;
  - the rest: about 300 s, or less when the remaining budget was shorter.

  The per-arm 5,400 s cap bounded the run. The call times are measured around HiGHS's `run()`, so these are overruns
  inside the solver.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| W1 | cold accepts at most 2 moves, reproducing the stall | **false** (4): with direct HiGHS there is no stall |
| W2 | warm returns a feasible point on every repair | true (16 / 16) |
| W3 | warm accepts more improving moves than cold | **false** (4 = 4, identical trajectory) |
| W4 | warm lowers fit by less than 1% | true (−0.96%) |
| W5 | warm: 0 fit worse, and at most 5 dev-val worse than the seed | true (0 and 0) |
| W6 | neither arm becomes the new current best | true |

## What this shows and does not show

- **Shows.** With item 26's direct-HiGHS model, the nonregression constraint is productive. It gives a successor of
  item 13 that improves 26 dev-val programs and worsens none. A breadth-protecting exact repair therefore exists,
  and in items 22 and 29 it was blocked by the solver interface, not by the constraint. This changes how items 22 and
  29's nonregress rows should be read: as a SciPy wrapper or configuration outcome.
- **Does not show:**
  - which factor of the interface matters;
  - that the gain transfers, since this is consumed-development evidence from an adaptive seed;
  - anything about the M1 gates, which are still far away (median 32, p95 96, 10%).

  It also does not show the same repair on item 24, the current best. Stacking it there is the natural next step and
  needs its own freeze. A successor here can only motivate an owner-approved, separately frozen confirmation.
