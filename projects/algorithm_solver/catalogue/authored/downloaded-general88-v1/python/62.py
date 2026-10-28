"""62. Unique Paths (Medium).

Specification: https://leetcode.com/problems/unique-paths/description/
"""


def solve(m: int, n: int) -> int:
    dp = [1] * n
    for _r in range(1, m):
        for c in range(1, n):
            dp[c] += dp[c - 1]
    return dp[n - 1]


class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        return solve(m, n)
