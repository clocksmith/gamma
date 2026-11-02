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
self-agreement; the brute-force cross-check is the independent evidence. Known gaps: several multi-answer problems are compared exactly against the
reference order; the generated maximum rows are far
below the public limits.

## Native-ABI split and lineage reconciliation (appended 2026-11-02)

`solve(...)` is the pure value-domain entrypoint (`solve_effects`: input mutation and output aliasing forbidden);
the official entry implements the LeetCode ABI. Copies made to keep `solve` pure, or to adapt it to the native ABI,
are charged in each semantics file's `charged_costs` and `complexity_target`.

- 156: `solve` deep-copies a native `TreeNode` input (iterative, with a seen map that rejects a node reached twice)
  before the rotation, so the result shares no node with the caller's tree. `upsideDownBinaryTree` /
  `Solution.upsideDownBinaryTree` rotates the caller's tree in place (`native_effects.mutates_inputs: true`).
- 280: `wiggleSort` / `Solution.wiggleSort` rewrites `nums` in place and returns nothing. `contracts.json` and the
  semantics declare `official_interface.in_place_arg: 0`; `run_candidates.py` judges that entry on
  `args_after[0] == expected` with other arguments unchanged, while `solve` must still leave its arguments unchanged
  and return the expected value.
- 286: `wallsAndGates` / `Solution.wallsAndGates` applies the same split, rewriting `rooms` in place row by row
  (`in_place_arg: 0`); `solve` still returns a new grid.
- 903: `manifest.json` `source_inventory` and `authoring-catalog.json` had kept the pre-fix hashes. They now carry the
  corrected hashes, with the pre-fix hashes, prior catalog variant IDs, freeze amendments and history blobs under
  explicit `supersedes` entries.

Every changed file has a dated amendment in `pre-source-reference-freeze.json`; superseded bytes are retained in
`study-history/blobs/`. `../../development-66-20261029-v1/revise-cohort-lineage.py` performed the rebinding and
`../../development-66-20261029-v1/check_native_abi.py` is the regression gate (a gate over declared contracts, not a
purity proof or qualification). Qualification stays unknown.

The read-only tree problems 742, 1214 and 1740 declare `solve_effects` and read-only `native_effects`; the checker
drives them on foreign node objects. Their sources are unchanged.

String units are pinned in semantics: `unicode_codepoint` for 159, 161, 758 and 1933 (non-BMP canary rows in
`cases.py`; JavaScript 159, 161 and 1933 now iterate code points), `ascii` for 294, 751, 772 and 903 (official
domains), and `opaque` for 737 (whole-string equality only).

1924's reference and Python candidate now return float centre coordinates for a single or duplicated point
(previously `[3, 3, 0.0]`). 774, 1230 and 1924 semantics pin the official absolute tolerance (1e-6, 1e-5, 1e-5) as a
`float_abs_tolerance` comparator; `run_candidates.py` still requires exact agreement with the rounded reference, which
is stricter.


```sh
python3 test_oracles.py
python3 run_candidates.py > /dev/null
python3 crosscheck_bruteforce.py > /dev/null
```
