"""3290. Maximum Multiplication Score (Medium).

Specification: https://leetcode.com/problems/maximum-multiplication-score/description/
"""


def solve(a: list[int], b: list[int]) -> int:
    NEG = float('-inf')
    dp = [0, NEG, NEG, NEG, NEG]
    for x in b:
        for t in range(4, 0, -1):
            if dp[t - 1] != NEG:
                dp[t] = max(dp[t], dp[t - 1] + a[t - 1] * x)
    return dp[4]


class Solution:
    def maxScore(self, a: list[int], b: list[int]) -> int:
        return solve(a, b)
