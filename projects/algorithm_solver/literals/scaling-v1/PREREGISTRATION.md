# scaling-v1: predicting where token gain stops beating BPE, from training data alone

Frozen 2026-11-27 before any confirmatory chain was scored, before predictions for the confirmatory sizes were
computed, and before any file of the test pool was opened by any session.

## Question

Exact-parser token gain (open, lazy greedy, `fixed-source-v3` `greedy-entry`, policy `s1-whole`, L = 16) beats BPE
(same engine, mode `bpe`) at small fragment counts and loses at large ones. K* is the smallest fragment count k on a
50-fragment grid from which open uses more tokens than BPE at every larger grid point, refined to 10 fragments
(`explore_scaling.py`). Can K* be predicted from the training files and the open chain alone, without held-out data?

## Development evidence (already seen)

Eight points: CodeNet `primary` subsets of 50, 100, 150, 200 problems scored on CodeNet `dev`; catalogue training
subsets of 50, 100, 200, 400 problems scored on catalogue `dev` (`out/dev-scaling-*.json`). K* grows about as
N^0.75 to N^0.8 and its bytes per slot are not constant (86.6 to 185.0). The onset statistic (`explore_onset.py`,
`out/dev-onset-*.json`) at threshold 0.6, window 200 and scale 0.913 predicts all eight within 10.4% (mean 4.7%);
constant bytes per slot (B1) misses by up to 49.7%.

## Frozen rule and baselines (`predict.py`)

- **Onset:** K_0.6 = first k at which at least 60% of the 200 open fragments ending at k occur in exactly one training
  problem's text; prediction round(K_0.6 / 0.913).
- **B1:** round(N / 123.6), N = training bytes.
- **B2:** round(exp(-1.810) N^0.743), a power law fitted on the four catalogue development sizes (it uses held-out
  sweeps; the onset rule does not).

## Confirmatory test

- Training: the first 800, 1,600 and 2,269 catalogue training problems (`sets/catalogue-train.json`, nested), open
  and BPE chains to 16,384, 24,576 and 32,768 entries, engine `build_engine.sh` (frozen engine, file cap raised only).
- Deciding set: the sealed catalogue test pool, 600 problems (`sets/catalogue-test.json`), never opened before
  `score.py` runs. Secondary: catalogue dev.
- **Pass:** the onset prediction is within 20% of the test-pool K* at every size, and its mean absolute log error is
  below B1's. Whether it beats B2 is reported, not decisive. A size whose K* or prediction is undefined counts as a
  miss.
- Order: chains finish; `predict.py` writes `out/predictions.json` (training data only) and it is committed; then a
  separate agent session runs `score.py` and nothing else.

## Limits

The catalogue solutions were written by agents in this project. Builder, rule fitting and holdout split are one
author; the split is a hash rule committed with this file; the scorer is a separate agent session running frozen code,
not an independent party. The test pool is a different set of problems from the same catalogue, not a different
domain.
