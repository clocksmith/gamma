"""64. Minimum Path Sum (Medium).

Specification: https://leetcode.com/problems/minimum-path-sum/description/
"""


def solve(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    dp = [[0] * n for _ in range(m)]
    for r in range(m):
        for c in range(n):
            if r == 0 and c == 0:
                dp[r][c] = grid[r][c]
            elif r == 0:
                dp[r][c] = dp[r][c - 1] + grid[r][c]
            elif c == 0:
                dp[r][c] = dp[r - 1][c] + grid[r][c]
            else:
                dp[r][c] = min(dp[r - 1][c], dp[r][c - 1]) + grid[r][c]
    return dp[m - 1][n - 1]


class Solution:
    def minPathSum(self, grid: list[list[int]]) -> int:
        return solve(grid)
