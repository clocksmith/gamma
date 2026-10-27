"""3974. Maximum Total Sum of K Selected Elements
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-total-sum-of-k-selected-elements/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3974.Maximum%20Total%20Sum%20of%20K%20Selected%20Elements/README_EN.md
Complexity: O(n log n) time, O(n) space.
All values are positive. Choose k largest and match descending values to descending effective multipliers. Answer <= 1e15 is exactly representable; inputs preserved.
"""

from __future__ import annotations

def solve(nums, k, mul):
    ordered = sorted(nums, reverse=True)
    return sum(ordered[index] * max(1, mul - index) for index in range(k))


class Solution:
    def maxSum(self, nums, k, mul):
        return solve(nums, k, mul)
