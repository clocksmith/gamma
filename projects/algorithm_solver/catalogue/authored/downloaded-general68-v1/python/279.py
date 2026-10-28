"""279. Perfect Squares (Medium).

Specification: https://leetcode.com/problems/perfect-squares/description/
"""


def solve(n: int) -> int:
    dp = [float('inf')] * (n + 1)
    dp[0] = 0
    for value in range(1, n + 1):
        root = 1
        while root * root <= value:
            dp[value] = min(dp[value], dp[value - root * root] + 1)
            root += 1
    return dp[n]


class Solution:
    def numSquares(self, n: int) -> int:
        return solve(n)
