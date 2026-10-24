# python-slackcap-v1: bounded relaxation of the per-program caps for the Python repair (board item 74, T4)

[Freeze](FREEZE.md) `8275f594b`. **Review:** a fresh-context Claude subagent stood in for codex, who is out until
2026-10-30, and found no blocker. The run started at 15:28:07Z and ended at 15:43:09Z on cores 0, 1, 2 and 4. Each arm
used its 900 s budget, and all exited 0.

**Disclosed pre-launch run:** one evidence stand-in, in which each arm carried its unchanged start dictionary. It
reproduced 914 and 1,395 actions; receipt `python-slackcap/standin-prelaunch/evidence-results.json`, `64f40646…`.

[evidence.py](evidence.py):
- verifies the contract;
- re-evaluates every sealed dictionary independently;
- reconciles every counter, the new maximum fit worsening included;
- checks the slack and fraction invariants. No arm failed.

[Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

## Result: the slack opens real fit gains, and validation gets worse in every arm

| Arm | Moves / accepted | Fit N (start) | Fit programs better / worse | Dev-val actions (start) | Median / p90 | Single-char | vs start | vs anchor incrementals |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| w8s1 | 62 / 17 | 1,905 (1,925) | 14 / 8 | **922** (914) | 103 / 179 | 56.85% | 5 / 1 / 3 | fail (median) |
| w8s3 | 77 / 19 | 1,897 (1,925) | 14 / 7 | **928** (914) | 100 / 183 | 57.78% | 4 / 0 / 5 | fail |
| w7s1 | 27 / 2 | 3,611 (3,617) | 9 / 6 | **1,397** (1,395) | 126 / 248 | 73.85% | 3 / 2 / 4 | pass |
| w7s3 | 28 / 2 | 3,570 (3,617) | 11 / 8 | **1,397** (1,395) | 126 / 253 | 73.85% | 5 / 1 / 3 | pass |

- **The fit gains are real.** At w8 the s = 0 neighbourhoods were exhausted: item 73's random arm accepted 1 move out of
  61. Here s = 1 accepts 17 moves and s = 3 accepts 19, lowering fit selections by 20 and 28. At w7, s = 3 lowers them
  by 47.
- **They do not transfer.** Every arm ends with **more** validation actions than its start, item 69's dictionary.
  Three to five of the 9 validation programs get worse in each arm. Larger slack buys more fit gain and, at w8, a
  larger validation loss.
- **Gates.** The w7 arms still pass the incrementals against the item 31 anchor (1,397 against 1,420), but they are
  worse than item 69's 1,395. The w8 arms fail the anchor incrementals on the median. No arm is ready against R.
- **Matched pairs, s = 3 against s = 1.** Validation is 2 / 3 / 4 at w8 and 3 / 2 / 4 at w7.
- **Controls.** These are item 73's w8rnd and w7rnd, descriptive only. w7rnd is an exact s = 0 control, since it
  accepted nothing. w8rnd is exact only up to its single accepted move: item 73 ratcheted caps to the incumbent, while
  s = 0 here would keep them at the start (review note).

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| S1 | some slack arm accepts at least 1 move | true |
| S2 | some slack arm reaches fewer validation actions than its start | **false** |
| S3 | some slack arm makes a validation program worse than its start | true (every arm) |
| S4 | some arm passes every anchor incremental **and** improves on its start | **false** |
| S5 | no arm ready against R | true |

## What this shows and does not show

- **Shows.** Around item 69's Python dictionaries, the capped neighbourhoods of items 70 and 73 are not just a solver
  limit. Relaxing the caps finds fit-total gains readily, but on the 9 validation programs those gains are
  redistributions that overfit the 27 fit programs. The nonregression caps were what kept repair moves
  validation-safe. Extra fit-only search from these dictionaries is now unproductive in all three tested forms: random,
  related and slack-relaxed.
- **Does not show** anything about larger widths, source-side rewrites, a different fit/validation split, or JS. Nine
  validation programs are a small sample. Validation consumed here is adaptive development, not confirmation.
