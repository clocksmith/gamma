"""4033. Valid K-Unique Subarrays I
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/valid-k-unique-subarrays-i/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4033.Valid%20K-Unique%20Subarrays%20I/README_EN.md
Complexity: O(q log q + (n+q) sqrt(n)) time, O(n+q+max(nums)) space.
Exact Mo frequency accounting; no probabilistic parity hashes. Maximum-size runtime is not measured. Inputs preserved.
"""

from __future__ import annotations
from math import isqrt

def solve(nums, k, queries):
    width = max(1, isqrt(len(nums)))
    order = sorted(range(len(queries)), key=lambda q: (
        queries[q][0] // width,
        queries[q][1] if (queries[q][0] // width) % 2 == 0 else -queries[q][1]))
    frequency = [0] * (max(nums) + 1)
    left, right = 0, -1
    distinct = odd = 0
    answer = [False] * len(queries)
    def change(index, delta):
        nonlocal distinct, odd
        x = nums[index]
        old = frequency[x]
        new = old + delta
        odd += (new & 1) - (old & 1)
        distinct += (new > 0) - (old > 0)
        frequency[x] = new
    for q in order:
        a, b = queries[q]
        while left > a:
            left -= 1
            change(left, 1)
        while right < b:
            right += 1
            change(right, 1)
        while left < a:
            change(left, -1)
            left += 1
        while right > b:
            change(right, -1)
            right -= 1
        answer[q] = distinct == k and odd == 0
    return answer
