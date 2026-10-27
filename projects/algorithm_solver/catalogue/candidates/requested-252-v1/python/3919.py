"""3919. Minimum Cost to Move Between Indices
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-cost-to-move-between-indices/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3919.Minimum%20Cost%20to%20Move%20Between%20Indices/README_EN.md
Complexity: O(n+q) time and space.
Strictly increasing signed nums; closest ties go left. Distinct directional prefix costs. No mutation.
"""

from __future__ import annotations

def solve(nums, queries):
    n = len(nums)
    right = [0] * n
    left = [0] * n
    for index in range(1, n):
        gap = nums[index] - nums[index - 1]
        right_cost = gap if index > 1 and nums[index - 1] - nums[index - 2] <= gap else 1
        left_cost = gap if index + 1 < n and nums[index + 1] - nums[index] < gap else 1
        right[index] = right[index - 1] + right_cost
        left[index] = left[index - 1] + left_cost
    return [right[end] - right[start] if start <= end else left[start] - left[end] for start, end in queries]


class Solution:
    def minCost(self, nums, queries):
        return solve(nums, queries)
