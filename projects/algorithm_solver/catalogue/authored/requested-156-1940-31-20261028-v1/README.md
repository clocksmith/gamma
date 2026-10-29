# Requested 156-1940 (31 Gate-Allowed Problems — Batches 1 + 2b): candidate source pairs

Original Python and JavaScript candidate implementations for 31 gate-allowed LeetCode IDs:
156, 159, 161, 163, 280, 286, 294, 737, 742, 751, 755, 758, 772, 774, 903, 911,
1213, 1214, 1215, 1229, 1230, 1692, 1714, 1740, 1820, 1826, 1908, 1918, 1924,
1933, and 1940.

Qualification status for all 62 candidate sources is `unknown`. No qualification
is claimed.

## Candidate runs and a reference correction (appended 2026-10-29)

`run_candidates.py` ran every candidate on every generated case (`cases.build_cases(pid, include_maximum=True)`, 117
rows) under python3 and `node --jitless`, through `solve` and through the official `Solution` method, named export or
native `TopVotedCandidate` class, with a fresh copy of the arguments per call. All 117 rows pass in both languages
through both entries, inputs are unchanged after every call, and no call used more than 1 s of CPU (heaviest: 774 at
0.0005 s). Per-problem results, source hashes and timings are in `checks.json`. These are author-local runs, not
isolated or independent qualification; qualification status stays unknown.

903 was wrong in the reference and in both candidates: the I step did not add the new lowest rank (for example DID
gave 3, not 5). The first run passed because the candidates repeat the reference. Study examples written by hand
exposed the disagreement, and enumerating permutations confirmed it. `oracles.py`, `python/903.py`,
`javascript/903.js` and the two 903 semantics hashes were corrected; old and new hashes are in the `amendments` of
`pre-source-reference-freeze.json`. After the change, `crosscheck_bruteforce.py` finds no mismatch on 4622 seeded random
small inputs across all 31 references, and every candidate passes again.

The Python `solve` bodies of 24 problems repeat the reference statement for statement, so agreement there is
self-agreement; the brute-force cross-check is the independent evidence. Known gaps: 280 and 286 return new
values instead of modifying the input in place as the public interfaces do; 1924 returns integer centre coordinates for
a single point; several multi-answer or tolerance problems are compared exactly; the generated maximum rows are far
below the public limits.


```sh
python3 test_oracles.py
python3 run_candidates.py > /dev/null
python3 crosscheck_bruteforce.py > /dev/null
```
