# Gamma hard-problem candidates: JavaScript + Python

**Batch:** HARD10-20261025  
**Status:** 10 solved problem candidates, 20 implementations; local validation passed. **Not Gamma-qualified or admitted.**

The selected problems are all officially labelled Hard and appear in Gamma's exposed development-fit partition. Selection and canonical interface were checked against `clocksmith/gamma` at commit `7290ac480db36698b4c69e677f4f51172dd738bd`. The published protected identifiers and family names were checked before problem-content lookup. No final-heldout or protected problem payload, source answer, or independent test was read.

## Interface and file layout

Each numbered JavaScript and Python file exposes a synchronous `solve(...)` function with positional arguments in the same order. JavaScript also exposes the standard named LeetCode function and guarded CommonJS exports. Python also provides `Solution.<nativeMethod>(...)`. All 20 source files are self-contained; Python imports only the standard library. Node.js with BigInt support and Python 3.9+ are required. Local validation actually ran on the versions recorded in `validation/latest-report.json`.

| ID | Problem | Canonical call, both languages | Native function / Solution method | Time | Auxiliary space |
|---|---|---|---|---|---|
| 10 | Regular Expression Matching | `solve(s, p)` | `isMatch` | O(len(s) * len(p)) | O(len(p)) |
| 42 | Trapping Rain Water | `solve(height)` | `trap` | O(n) | O(1) |
| 84 | Largest Rectangle in Histogram | `solve(heights)` | `largestRectangleArea` | O(n) | O(n) |
| 85 | Maximal Rectangle | `solve(matrix)` | `maximalRectangle` | O(rows * columns) | O(columns) |
| 123 | Best Time to Buy and Sell Stock III | `solve(prices)` | `maxProfit` | O(n) | O(1) |
| 546 | Remove Boxes | `solve(boxes)` | `removeBoxes` | O(n^4) worst case | O(n^3) memo plus O(n) stack |
| 564 | Find the Closest Palindrome | `solve(n)` | `nearestPalindromic` | O(d) string work plus a constant number of exact d-digit arithmetic operations; d <= 18 | O(d) |
| 992 | Subarrays with K Different Integers | `solve(nums, k)` | `subarraysWithKDistinct` | O(n) expected with hash maps | O(n) |
| 1074 | Number of Submatrices That Sum to Target | `solve(matrix, target)` | `numSubmatrixSumTarget` | O(min(rows, columns)^2 * max(rows, columns)) expected with hash maps | O(max(rows, columns)) |
| 1187 | Make Array Strictly Increasing | `solve(arr1, arr2)` | `makeArrayIncreasing` | O(m log m + n^2 log(m + 1)) worst case | O(n + m) |

Every implementation preserves input values and nested-container identities. Python uses idiomatic snake_case internal variables and exact native method names; JavaScript uses two-space indentation, semicolons and descriptive camelCase. No external helper package, network call, module-global answer cache, or hidden problem dispatch is required.

- `javascript/`: 10 `.js` candidates and 10 six-field semantics records.
- `python/`: 10 `.py` candidates and 10 six-field semantics records.
- `contracts/`: per-problem public-domain contract summaries; these are **candidate contracts**, not forged Gamma frozen-contract receipts.
- `assignment.json`: chosen IDs, parameter order, native APIs, complexity and pinned repository identity.
- `provenance/selection.json` and `REFERENCES.md`: metadata eligibility and exact source references.
- `validation/`: self-authored reproducible cases, independent-method oracles, input-only workers and retained outputs.
- `SHA256SUMS`: all distributed payload files, excluding the checksum file itself.

## Run the local checks

From this extracted directory:

```sh
python validation/validate.py
```

This uses the already supplied case files and creates a new numbered attempt instead of overwriting previous execution evidence. To regenerate the corpus from its fixed seed first:

```sh
python validation/build_cases.py
python validation/validate.py
```

The generated corpus uses seed `20261025`. A new attempt does not change the previously retained attempt report. Runtime timers are diagnostic local timings, not a cross-machine performance comparison or complexity proof.

## Validation boundary

Each case runs through JavaScript `solve`, its native alias, Python `solve`, and its native Solution method. Host-side code checks exact outputs, exact return type, unchanged input contents and unchanged nested-container identities. JavaScript integer answers must be safe integers. Candidate processes receive only the case ID and positional inputs; expected answers remain with the host-side evaluator.

Separate references enumerate intervals, rectangles, transaction schedules, legal box-removal segments, or replacement choices. Regex checks use Python's restricted `re.fullmatch` on valid patterns. Palindrome checking enumerates distance for small numbers and independently binary-searches ordered palindrome families for large numbers. Maximum-size cases use explicit closed-form expected values. These references were independently implemented in this batch, **not supplied or approved by an external verifier**.

Python and JavaScript agreement is an additional check, not the oracle. Native aliases are adapters, not additional unique implementations. Out-of-domain empty-input probes are reported separately and do not enlarge claimed normative coverage.

## Gamma integration handoff

The inspected catalogue requires `solve` with `ordered-positional` arguments and externally verified source/interface/runtime/test/effect bindings. These candidates meet that API shape. The public normative contracts were checked, but the selected IDs' **private frozen Gamma problem/effect contracts and actual test packs were not available in the inspected public files**. A coordinator must compare them before admission. In particular, do not silently reinterpret a frozen mutation or alias observation to fit these non-mutating candidates.

Use only the authorized source slots and the existing isolated judge. Preserve failed receipts and assign new candidate identities after a repair. Do not change expected outputs, test budgets, sandbox policy, protected populations or existing accepted sources to obtain a pass. This package does not contain a live qualification command pretending to know the user's local paths or runner contract.

No repository files, catalogue records, user machines, commits, deployments, models or training runs were changed. Solving these known problems in this chat is **not** an autonomous-composer result or a claim that Gamma's benchmark coverage increased.

## Algorithm reasoning and semantics

### 10. Regular Expression Matching

The previous row records which pattern prefixes match the already processed string. A starred atom either contributes no characters (two pattern symbols earlier on the current row), or consumes the new matching character while retaining the starred pattern (same column of the previous row). A plain atom extends a diagonal match. Initial nullable patterns handle empty prefixes. The final cell represents a complete, not substring, match.

**Semantics:** Lowercase ASCII and syntactically valid dot/star patterns only. Empty string/pattern probes are separate extensions.

### 42. Trapping Rain Water

Process the side whose current boundary is lower, maintaining the largest boundary already seen on that side. The opposite side or an already established opposing maximum provides the necessary enclosure, so the contribution at the processed bar is fixed. Each index is finalized once. No height is changed.

**Semantics:** Heights and the total trapped water remain exact JavaScript integers under the published bounds.

### 84. Largest Rectangle in Histogram

Indices on the stack have nondecreasing heights. When a lower bar arrives, a popped bar cannot extend past that position; the new stack top identifies its nearest smaller boundary on the left. The calculated width is maximal for that height. A virtual trailing zero processes all remaining positive bars without appending to the input.

**Semantics:** Equal heights, all-zero arrays, monotone arrays and large plateaus are covered.

### 85. Maximal Rectangle

For each row, a column height counts consecutive ones ending there. Every all-one rectangle has a bottom row, where it appears as a histogram rectangle. Applying the stack invariant to each row therefore examines a maximal candidate for every possible bottom edge. The matrix and row objects remain unchanged.

**Semantics:** The normative cells are strings "0" and "1", not numeric coercions. Empty matrices are only an extension probe.

### 123. Best Time to Buy and Sell Stock III

The four states describe the best balance after the first buy, first sale, second buy and second sale. Each step chooses between keeping a state and performing its next action at today’s price. Updating backwards prevents a transition from accidentally using a newly updated predecessor. Zero-profit sell states allow fewer than two transactions.

**Semantics:** Negative infinity is internal only. The result remains an integer, including zero for falling prices.

### 546. Remove Boxes

A state represents an interval of color runs plus matching boxes carried to its right. Either remove the rightmost run with its carried boxes now, or first remove the intervening interval and merge it into an earlier run of the same color. These cases cover the possible removal of the right boundary; memoization avoids repeated subproblems. Run compression preserves adjacent equal boxes, which need not be split in an optimum.

**Semantics:** Input length is at most 100. Recursion is confined to that bounded interval; this is not an unbounded-stack implementation.

### 564. Find the Closest Palindrome

Within a fixed digit length, palindromes are ordered by their leading half. The closest different palindrome must come from mirroring the input half or an adjacent half, unless the optimum crosses a digit-length boundary. Both boundaries are added explicitly. Compare exact absolute differences and select the smaller value on ties, excluding the input itself.

**Semantics:** JavaScript uses BigInt for the entire represented value and all distances. Inputs above 2^53 are never rounded through Number; output remains a string.

### 992. Subarrays with K Different Integers

Every subarray has a distinct-count integer. Subtracting the number with at most k-1 from those with at most k leaves exactly k. For a fixed right endpoint, once the left boundary makes a window valid, every later left boundary is valid too, contributing right-left+1 intervals. Both pointers advance monotonically.

**Semantics:** The at-most-zero helper correctly contributes zero nonempty windows. The total fits exact Number arithmetic.

### 1074. Number of Submatrices That Sum to Target

Choose two boundaries on the smaller dimension and sum cells between them into a one-dimensional line. A rectangle between those boundaries corresponds uniquely to an interval of that line. A previous prefix equal to currentPrefix-target yields one matching interval; its frequency counts duplicates. Iterating all boundary pairs covers all nonempty rectangles once.

**Semantics:** Handles negative values and repeated prefix sums, either matrix orientation, and preserves all matrix cells.

### 1187. Make Array Strictly Increasing

For each replacement count, only the smallest achievable last value needs to be retained: a larger one can never admit more future values. To replace the next element, the smallest arr2 value greater than the current tail is sufficient. A state is dominated when a cheaper state has an equal or smaller tail. Keep or replace transitions followed by this pruning preserve every potentially optimal completion.

**Semantics:** arr2 is copied, sorted and deduplicated; neither array is modified. Its values may be reused. A reachable final state returns the minimum count; an empty frontier returns -1.

