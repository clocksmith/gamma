"""300. Longest Increasing Subsequence (Medium).

Specification: https://leetcode.com/problems/longest-increasing-subsequence/description/
"""


def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    dp = [1] * len(nums)
    best = 1
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
        best = max(best, dp[i])
    return best


class Solution:
    def lengthOfLIS(self, nums: list[int]) -> int:
        return solve(nums)
