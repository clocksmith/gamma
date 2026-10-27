"""3909. Compare Sums of Bitonic Parts
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/compare-sums-of-bitonic-parts/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3909.Compare%20Sums%20of%20Bitonic%20Parts/README_EN.md
Complexity: O(n) time, O(1) auxiliary space.
Single-peak bitonic input; common peak cancels in comparison. Sums <=1e14; no mutation.
"""

from __future__ import annotations

def solve(nums):
    peak = 0
    while peak + 1 < len(nums) and nums[peak] < nums[peak + 1]:
        peak += 1
    left = sum(nums[index] for index in range(peak))
    right = sum(nums[index] for index in range(peak + 1, len(nums)))
    return -1 if left == right else 0 if left > right else 1


class Solution:
    def compareBitonicSums(self, nums):
        return solve(nums)
