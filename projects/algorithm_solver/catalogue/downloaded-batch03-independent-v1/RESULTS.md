# Downloaded third batch: qualification outcomes and gap analysis

This report summarizes the independent qualification evaluation for the 88 JavaScript/Python
pairs (176 programs) in `projects/algorithm_solver/catalogue/authored/downloaded-general88-v1/`.

## Summary of Qualification Outcomes

| Metric | Python | JavaScript | Total |
|---|---|---|---|
| Total Programs Evaluated | 88 | 88 | 176 |
| Prepared Test Cases | 1,512 | 1,512 | 1,512 |
| Distinct Functional Cases Passed | 1,512 (100%) | 1,512 (100%) | 3,024 / 3,024 |
| Input Mutation Failures (`args_before != args_after`) | 0 | 0 | 0 |
| Mutable Return Alias Failures (`alias_edges != []`) | 0 | 0 | 0 |
| Functional Return-Value Adapters Distinguished | 10 | 10 | 20 |
| Mandatory Complexity / Space Failures | 3 | 3 | 6 |
| Formally Qualified Functional Programs | 85 / 88 | 85 / 88 | 170 / 176 |
| Platform Judge Execution Status | Unexecuted | Unexecuted | Unexecuted |

## Concrete Gaps and Mandatory Constraint Failures

Three problems fail mandatory algorithmic or complexity constraints stated in their official definitions:

1. **Problem 41 (First Missing Positive):**
   - *Requirement:* "You must implement an algorithm that runs in O(n) time and uses O(1) auxiliary space."
   - *Python candidate:* `seen = set(nums)` materializes an $O(n)$ hash set.
   - *JavaScript candidate:* `const seen = new Set(nums)` materializes an $O(n)$ Set.
   - *Outcome:* Fails mandatory constant auxiliary space gate.

2. **Problem 164 (Maximum Gap):**
   - *Requirement:* "You must write an algorithm that runs in linear time and uses linear extra space."
   - *Python candidate:* `ordered = sorted(nums)` uses Timsort ($O(n \log n)$ time).
   - *JavaScript candidate:* `nums.slice().sort((a, b) => a - b)` uses comparison sort ($O(n \log n)$ time).
   - *Outcome:* Fails mandatory linear time complexity gate.

3. **Problem 373 (Find K Pairs with Smallest Sums):**
   - *Requirement:* Input arrays $nums1, nums2$ have length up to $10^5$. Algorithm must avoid quadratic time and space.
   - *Python candidate:* `pairs = [[a, b] for a in nums1 for b in nums2]; pairs.sort(...)` materializes all $|nums1| \times |nums2|$ pairs into memory.
   - *JavaScript candidate:* `for (const a of nums1) for (const b of nums2) pairs.push([a, b]); pairs.sort(...)` materializes all pairs into memory.
   - *Outcome:* Fails subquadratic memory and time bounds.

## In-Place APIs vs. Functional Return-Value Adapters

Ten problems (IDs 26, 27, 31, 48, 73, 75, 80, 88, 130, 186) specify in-place modifications in LeetCode:
- In LeetCode, `removeDuplicates` (26, 80) and `removeElement` (27) modify the array in-place and return the integer length $k$.
- In LeetCode, `nextPermutation` (31), `rotate` (48), `setZeroes` (73), `sortColors` (75), `merge` (88), `solve` (130), and `reverseWords` (186) modify the input in-place and return `None` (void).
- The supplied candidates implement functional adapters: they do not modify the input arrays in-place, but return fresh arrays/matrices containing the transformed state.
- In `python/` and `javascript/`, the provided `Solution` class wrappers simply forward to `solve` and return its return value.
- These functional return-value adapters are qualified under local functional effect contracts (`args_before == args_after`, `alias_edges == []`). The official in-place wrappers are distinguished and not execution-qualified.

## Isolated Judge Platform Delivery

- Bubblewrap isolation judge (`/usr/bin/bwrap`) is unavailable on macOS Darwin.
- Per explicit charter instruction, candidates, test cases, and batch execution plans are frozen and delivered as unexecuted.
- The delivered artifacts provide complete, reproducible contracts that can be dispatched to an authorized Linux bubblewrap runner without modification.
