"""1027. Longest Arithmetic Subsequence (Medium).

Specification: https://leetcode.com/problems/longest-arithmetic-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    if len(nums) <= 2:
        return len(nums)
    dp = [{} for _ in nums]
    best = 2
    for i in range(len(nums)):
        for j in range(i):
            diff = nums[i] - nums[j]
            length = dp[j].get(diff, 1) + 1
            dp[i][diff] = max(dp[i].get(diff, 0), length)
            best = max(best, dp[i][diff])
    return best


class Solution:
    def longestArithSeqLength(self, nums: list[int]) -> int:
        return solve(nums)
