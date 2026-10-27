"""3904. Smallest Stable Index II
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/smallest-stable-index-ii/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3904.Smallest%20Stable%20Index%20II/README_EN.md
Complexity: O(n) time and space.
nums and k nonnegative <=1e9; inputs preserved.
"""

from __future__ import annotations

def solve(nums, k):
    suffix = nums.copy()
    for index in range(len(nums) - 2, -1, -1):
        suffix[index] = min(suffix[index], suffix[index + 1])
    largest = nums[0]
    for index, value in enumerate(nums):
        largest = max(largest, value)
        if largest - suffix[index] <= k:
            return index
    return -1


class Solution:
    def firstStableIndex(self, nums, k):
        return solve(nums, k)
