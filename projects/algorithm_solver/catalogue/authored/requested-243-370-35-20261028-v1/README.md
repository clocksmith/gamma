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

## 340 string unit (appended 2026-11-02)

340's semantics pin `string_unit: unicode_codepoint`. `javascript/340.js` now iterates `Array.from(s)` (an O(n)
code-point array, charged in its semantics) instead of UTF-16 code units, matching Python `str` iteration and
`ref_340`. `cases.py` adds three non-BMP rows whose expected values come from the unchanged reference, raising the
generated rows to 154 per language: `("\U0001F600a", 1)` expects 1; `("\U0001F600\U0001F600a", 1)` expects 2 and
`("a\U0001F600b\U0001F600", 2)` expects 3, where UTF-16 code units would give 1 and 2 (the previous JavaScript
candidate failed both). The amendments are dated in `pre-source-reference-freeze.json`; superseded bytes are in
`study-history/blobs/`. Qualification stays unknown.

## Native node effects (appended 2026-11-02)

369's `solve` copies a native `ListNode` input (a cycle is rejected) instead of incrementing the caller's list in
place; the old version also returned caller nodes and looped forever on a cyclic list. `plusOne` / `Solution.plusOne`
increments in place (`native_effects.mutates_inputs: true`). The tree problems 250, 270, 272, 298, 314, 333 and 366
were already read-only; their semantics now declare `solve_effects` and read-only `native_effects`, and
`../../development-66-20261029-v1/check_native_abi.py` exercises them on foreign node objects.


```sh
python3 run_candidates.py > /dev/null
python3 crosscheck_bruteforce.py > /dev/null
```
