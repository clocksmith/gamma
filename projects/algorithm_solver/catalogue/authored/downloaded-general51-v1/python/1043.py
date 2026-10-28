"""1043. Partition Array for Maximum Sum (Medium).

Specification: https://leetcode.com/problems/partition-array-for-maximum-sum/description/
"""


def solve(arr: list[int], k: int) -> int:
    dp = [0] * (len(arr) + 1)
    for i in range(1, len(arr) + 1):
        maximum = 0
        for length in range(1, k + 1):
            if length > i:
                break
            maximum = max(maximum, arr[i - length])
            dp[i] = max(dp[i], dp[i - length] + maximum * length)
    return dp[len(arr)]


class Solution:
    def maxSumAfterPartitioning(self, arr: list[int], k: int) -> int:
        return solve(arr, k)
