# Requested 243-370 (35 Problems — Batch 2a): candidate source pairs

Original Python and JavaScript candidate implementations for 35 gate-allowed LeetCode IDs:
243, 245, 246, 247, 248, 249, 250, 254, 255, 256, 259, 265, 267, 269, 270, 272,
276, 296, 298, 302, 311, 314, 317, 320, 325, 333, 340, 351, 356, 358, 360, 361,
366, 369, and 370.

Qualification status for all 70 candidate sources is `unknown`. No qualification
is claimed.

## Candidate runs (appended 2026-10-29)

`run_candidates.py` ran every candidate on every generated case (`cases.build_cases(pid, include_maximum=True)`, 151
rows) under python3 and `node --jitless`, through `solve` and through the official `Solution` method or named export,
with a fresh copy of the arguments per call. All 151 rows pass in both languages through both entries, inputs are
unchanged after every call, and no call used more than 1 s of CPU (heaviest: 351 at 0.004 s). Per-problem results,
source hashes and timings are in `checks.json`. These are author-local runs, not isolated or independent
qualification; qualification status stays unknown.

The Python `solve` bodies of 22 problems repeat the reference statement for statement, so agreement there is
self-agreement. `crosscheck_bruteforce.py` therefore compares the references with independent brute-force
restatements on 5140 seeded random small inputs; there were no mismatches. No candidate, reference, case or
expected value changed. Known gaps: 302 scans in O(m*n) although the public problem asks for less; several
multi-answer problems are compared exactly against the reference's order; the generated maximum rows are far below
the public limits.


```sh
python3 run_candidates.py > /dev/null
python3 crosscheck_bruteforce.py > /dev/null
```
