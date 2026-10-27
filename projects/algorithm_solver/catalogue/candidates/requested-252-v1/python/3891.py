"""3891. Minimum Increase to Maximize Special Indices
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-increase-to-maximize-special-indices/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3891.Minimum%20Increase%20to%20Maximize%20Special%20Indices/README_EN.md
Complexity: O(n) time, O(1) auxiliary space.
Maximizes nonadjacent interior peak count before minimizing cost. Sum <= 1e14; input preserved.
"""

from __future__ import annotations

def solve(nums):
    # Store (negative peak count, cost), so ordinary tuple minimum is the objective.
    skip = (0, 0)
    take = (1, 0)
    for index in range(1, len(nums) - 1):
        cost = max(0, max(nums[index - 1], nums[index + 1]) + 1 - nums[index])
        skip, take = min(skip, take), (skip[0] - 1, skip[1] + cost)
    return min(skip, take)[1]


class Solution:
    def minIncrease(self, nums):
        return solve(nums)
