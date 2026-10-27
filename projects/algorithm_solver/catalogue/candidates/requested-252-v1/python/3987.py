"""3987. Minimum Total Cost to Process All Elements
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/minimum-total-cost-to-process-all-elements/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3987.Minimum%20Total%20Cost%20to%20Process%20All%20Elements/README_EN.md
Complexity: O(n) time, O(1) auxiliary integers.
Positive demands permit just-in-time replenishment; total required top-ups determine the triangular cost. BigInt prevents overflow before modulo. Inputs preserved.
"""

from __future__ import annotations

def solve(nums, k):
    operations = max(0, (sum(nums) + k - 1) // k - 1)
    return operations * (operations + 1) // 2 % 1_000_000_007


class Solution:
    def minimumCost(self, nums, k):
        return solve(nums, k)
