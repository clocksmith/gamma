"""1218. Longest Arithmetic Subsequence of Given Difference (Medium).

Specification: https://leetcode.com/problems/longest-arithmetic-subsequence-of-given-difference/description/
"""


def solve(arr: list[int], difference: int) -> int:
    dp = {}
    best = 0
    for value in arr:
        length = dp.get(value - difference, 0) + 1
        dp[value] = length
        best = max(best, length)
    return best


class Solution:
    def longestSubsequence(self, arr: list[int], difference: int) -> int:
        return solve(arr, difference)
