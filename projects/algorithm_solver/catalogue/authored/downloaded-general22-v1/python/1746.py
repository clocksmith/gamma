"""1746. Maximum Subarray Sum After One Operation (Medium).

Specification: https://leetcode.com/problems/maximum-subarray-sum-after-one-operation/description/
"""


def solve(nums: list[int]) -> int:
    f = 0
    g = 0
    best = float('-inf')
    for x in nums:
        ff = max(f, 0) + x
        gg = max(max(f, 0) + x * x, g + x)
        f, g = ff, gg
        best = max(best, f, g)
    return best


class Solution:
    def maxSumAfterOperation(self, nums: list[int]) -> int:
        return solve(nums)
