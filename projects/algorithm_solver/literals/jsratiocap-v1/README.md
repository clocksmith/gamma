# jsratiocap-v1: item 69's binary-arc ratio-versus-lex repair on the JS current best (board item 72, T3)

[Freeze](FREEZE.md) `ba7b48be6` and [amendment 1](AMENDMENT-1.md) `301484104`, which adds exact row checks on the
rounded integral point. **Review:** a fresh-context Claude subagent stood in for codex, who is out until 2026-10-30, and
found no blocker. The run started at 15:03:59Z and ended at 15:54:09Z on cores 8–11. Each arm used its 3,000 s budget,
and all exited 0.

**Disclosed pre-launch runs:**
- A fit-only runner smoke, `--smoke 1`: one 1 s move per arm, none accepted. Its output was discarded.
- An evidence stand-in, in which each arm carried item 51's unchanged dictionary. It reproduced 8,283 actions at
  49.505%; receipt `jsratiocap/standin-prelaunch/evidence-results.json`, `0637b528…`.

[evidence.py](evidence.py):
- verifies the contract;
- checks that the seed's fresh replay equals item 51's published per-program actions and aggregates;
- replays all 400 programs;
- reconciles every counter with the move logs;
- checks the nonregression and fit-fraction invariants. No arm failed.

The record-time binding is explicit, to item 51's evidence (`c287fe48…`, arm flat), the current best at record time.
[Evidence](evidence/results.json) (`48df3fd2…`) holds only aggregates, IDs and hashes.

## Result: no successor; capped fit gains make dev-val slightly worse

| Arm | Moves / accepted | Repairs optimal | Fit N / C (seed 24,069 / 11,997) | Fit programs better | Dev-val actions (seed 8,283) | Median / p90 actions | Single-char | vs seed |
| --- | --- | --- | --- | ---: | ---: | --- | ---: | --- |
| k40ratio | 11 / 1 | 3 | 24,053 / 11,985 | 16 | 8,290 | 63.5 / 154 | 49.573% | 5 / 93 / 2 |
| k40lex | 11 / 1 | 5 | 24,053 / 11,985 | 16 | 8,290 | 63.5 / 154 | 49.573% | 5 / 93 / 2 |
| k24ratio | 16 / 2 | 15 | 24,047 / 11,982 | 18 | 8,286 | 63.5 / 154 | 49.572% | 6 / 92 / 2 |
| k24lex | 17 / 2 | 15 | 24,047 / 11,982 | 18 | 8,286 | 63.5 / 154 | 49.572% | 6 / 92 / 2 |

- **The ratio row never bound.** At each k, the ratio arm ended on exactly the same dictionary as its lex control:
  `9145bfb6…` at k40 and `d42202a6…` at k24. The lex moves already lowered the fit fraction (49.844% → 49.827%),
  and there were no ratio rejections.
- **The fit gains are real and capped.** No fit program got worse, 16–18 got better, and fit N fell by 16 or 22.
  This is more than item 51's own continuation found (−5).
- **They do not transfer.** Dev-val gets worse by 3–7 actions:
  - median actions 62.5 → 63.5;
  - single-character fraction 49.505% → 49.57%;
  - 2 programs worse and 5–6 better.
- **Gates.** Every arm stays ready against R, but fails the incremental checks against item 51 on actions, median and
  fraction, so there is no successor. The record-time replacement has no candidate, and **item 51 stays the current
  best**.
- **Binary arcs cost little at k = 24** (15 of 16–17 repairs optimal), but heavily at k = 40 (3–5 of 11).

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| J1 | some ratio arm accepts at least 1 move | true |
| J2 | some ratio arm's dev-val fraction at most 49.505% | **false** (49.572%) |
| J3 | some ratio arm is a successor of item 51 | **false** |
| J4 | at both k, the lex control reaches no more dev-val actions than the ratio arm | true (identical) |
| J5 | full coverage, no failure | true |
| J6 | every ratio arm solves fewer than half its repairs to optimality | **false** (k24: 15 of 16) |

## What this shows and does not show

- **Shows.** Around item 51, item 69's ratio mechanism is inert on JS: the lex moves already lower the fit fraction.
  The extra capped fit gains that binary arcs and a fresh seed find (−16 to −22 selections) do not reduce dev-val
  actions, and they raise the dev-val median and fraction slightly. Python items 70 and 74 showed the same thing:
  fit-only repair from the current best dictionaries has stopped transferring to validation.
- **Does not show** anything about other neighbourhoods, source-side changes or confirmation. The M1 gap is unchanged:
  median 61.5 against 32, p95 195 against 96, fraction 49.5% against 10%.
