# scaling-v1 results

Scored 2026-11-27 by a separate agent session running the frozen `score.py` after `shasum -c` of every frozen file
and chain (preregistration `4d0a4c0d7`, predictions `c8c565555`, procedural deviation `d202cff6f`, see DEVIATIONS.md).
Output: `out/test-results.json`, `out/dev-scaling-test-confirm.json`, `out/dev-scaling-dev-confirm.json`.

## The preregistered prediction failed

| Training problems | Training bytes | K* test pool | K* dev | Onset prediction | B1 | B2 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 800 | 1,308,055 | 6,340 | 6,580 | 5,179 (-18.3%) | 10,583 (+66.9%) | 5,736 (-9.5%) |
| 1,600 | 2,574,842 | 13,460 | 14,160 | 8,176 (-39.3%) | 20,832 (+54.8%) | 9,487 (-29.5%) |
| 2,269 | 3,692,955 | 20,090 | 24,140 | 10,486 (-47.8%) | 29,878 (+48.7%) | 12,402 (-38.3%) |

Both criteria failed: the onset rule was outside 20% at two of three sizes, and its mean absolute log error (0.450) was
not below B1's (0.449). B2, the power law fitted on held-out sweeps, did better (0.311) but also undershot.

## What the measurements show

- The crossover grows faster than the development points implied. From 50 to 400 catalogue problems K* grew about as
  N^0.74; from 800 to 2,269 it grew about as N^1.1, at 184 to 206 training bytes per slot on the test pool.
- The onset of single-problem picks moves more slowly than the crossover at large sizes, so the development scale
  factor does not carry over.
- The small-budget win is stable: open uses 13.1% to 13.6% fewer tokens than BPE at 84 fragments at every size.
- The large-budget loss shrinks with data: at each chain's last length, open is behind BPE by 5.0%, 2.5% and 1.7% on
  the test pool (4.8%, 1.9%, 0.9% on dev). Near the crossover the two curves are almost parallel, so K* is poorly
  conditioned there: test and dev K* differ by 4% at 800 problems and by 20% at 2,269.

These are observations from one catalogue of agent-authored solutions; they are not a fitted law.
