"""3976. Maximum Subarray Sum After Multiplier
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-subarray-sum-after-multiplier/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3976.Maximum%20Subarray%20Sum%20After%20Multiplier/README_EN.md
Complexity: O(n) time, O(1) space.
Exact one nonempty operation, truncation toward zero. A nonworsening operation can always intersect an optimal sum segment for k >= 1. All sums within 1e15; inputs preserved.
"""

from __future__ import annotations

def solve(nums, k):
    before = multiplied = divided = after = float('-inf')
    answer = float('-inf')
    for value in nums:
        quotient = value // k if value >= 0 else -((-value) // k)
        new_before = max(0, before) + value
        new_multiplied = max(0, before, multiplied) + value * k
        new_divided = max(0, before, divided) + quotient
        new_after = max(multiplied, divided, after) + value
        before, multiplied, divided, after = new_before, new_multiplied, new_divided, new_after
        answer = max(answer, multiplied, divided, after)
    return answer


class Solution:
    def maxSubarraySum(self, nums, k):
        return solve(nums, k)
