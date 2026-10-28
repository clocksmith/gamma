"""416. Partition Equal Subset Sum (Medium).

Specification: https://leetcode.com/problems/partition-equal-subset-sum/description/
"""


def solve(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2 != 0:
        return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for value in nums:
        for s in range(target, value - 1, -1):
            dp[s] = dp[s] or dp[s - value]
    return dp[target]


class Solution:
    def canPartition(self, nums: list[int]) -> bool:
        return solve(nums)
