"""931. Minimum Falling Path Sum (Medium).

Specification: https://leetcode.com/problems/minimum-falling-path-sum/description/
"""


def solve(matrix: list[list[int]]) -> int:
    dp = matrix[0][:]
    for r in range(1, len(matrix)):
        nxt = []
        for c in range(len(matrix[r])):
            best = dp[c]
            if c > 0:
                best = min(best, dp[c - 1])
            if c + 1 < len(dp):
                best = min(best, dp[c + 1])
            nxt.append(matrix[r][c] + best)
        dp = nxt
    return min(dp)


class Solution:
    def minFallingPathSum(self, matrix: list[list[int]]) -> int:
        return solve(matrix)
