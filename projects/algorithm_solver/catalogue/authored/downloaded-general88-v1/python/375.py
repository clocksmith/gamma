"""375. Guess Number Higher or Lower II (Medium).

Specification: https://leetcode.com/problems/guess-number-higher-or-lower-ii/description/
"""


def solve(n: int) -> int:
    dp = [[0] * (n + 2) for _ in range(n + 2)]
    for length in range(2, n + 1):
        for start in range(1, n - length + 2):
            end = start + length - 1
            best = float('inf')
            for guess in range(start, end + 1):
                cost = guess + max(dp[start][guess - 1], dp[guess + 1][end])
                best = min(best, cost)
            dp[start][end] = best
    return dp[1][n]


class Solution:
    def getMoneyAmount(self, n: int) -> int:
        return solve(n)
