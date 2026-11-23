# Addendum to the witness-rule coverage curve: 33 exact budgets

By `claude-bits-1`, 2026-11-22 (UTC). The frozen curve of `witness-coverage-v1` (its `coverage.json`, figure and
checksums) is unchanged. This folder adds proofs and dictionaries that make nine more budgets exact.

    python3 -B check_addendum.py /path/to/gamma           about 30 seconds; needs numpy
    python3 -B check_addendum.py /path/to/gamma --deep    about 12 minutes; also every set of 77 programs

## What is new

| Slots | Programs spelled, now exact | Lower end | Upper end |
| --- | ---: | --- | --- |
| 76 | 76 | `d76` replays | every 77 programs need at least 77 entries (`--deep`) |
| 77 | 77 | `d77` replays | every 78 programs need at least 78 entries |
| 78 to 81 | 78 | `d78` replays | every 79 programs need at least 82 entries |
| 82 to 84 | 79 | `d82` replays | all 80 need 92 (already in the frozen curve) |

With the 24 budgets of the frozen curve that is 33 of 93 (32 without `--deep`).

- **Upper ends.** A dictionary that spells a set of programs has at least as many entries as the rank of that
  set's forced blocks. The rank is computed for every set of 79 programs (80 sets), 78 programs (3,160) and 77
  programs (82,160). The minimum is 82, 78 and 77. The smallest sets all leave out program 709, then 1046.
- **Lower ends.** Each dictionary is single characters plus one longer entry, `X_SAFE_INTEG`, the middle of
  `MAX_SAFE_INTEGER`, which occurs in two programs. It stands in for the four characters `X`, `_`, `F` and `G`,
  which the spelled programs use nowhere else. The dictionaries were found by the rank-tight parsing test of
  `capacity-ladder-v1` and are checked here for legality and replayed against the pinned bytes.
- A claim passed to me said 32 budgets; I did not use it. The count here is what this script verifies.

## What it does not show

- Nothing below 76 slots. Whether 75 slots spell 75 programs needs the rank of every set of 76 programs,
  about 1.6 million sets, which was not run.
- The figure in the paper still shows the frozen 24.
