"""446. Arithmetic Slices II - Subsequence (Hard).

Specification: https://leetcode.com/problems/arithmetic-slices-ii-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    total = 0
    dp = [{} for _ in nums]
    for i in range(len(nums)):
        for j in range(i):
            diff = nums[i] - nums[j]
            previous = dp[j].get(diff, 0)
            dp[i][diff] = dp[i].get(diff, 0) + previous + 1
            total += previous
    return total


class Solution:
    def numberOfArithmeticSlices(self, nums: list[int]) -> int:
        return solve(nums)
