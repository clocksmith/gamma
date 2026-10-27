"""3627. Maximum Median Sum of Subsequences of Size 3.

Specification: https://leetcode.com/problems/maximum-median-sum-of-subsequences-of-size-3/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O(n log n) time, O(n) space; length is divisible by three.
Inputs are not modified.
"""

def solve(nums):
    ordered = sorted(nums)
    return sum(ordered[len(ordered) - 2 - 2 * index] for index in range(len(ordered) // 3))


class Solution:
    def maximumMedianSum(self, nums):
        return solve(nums)
