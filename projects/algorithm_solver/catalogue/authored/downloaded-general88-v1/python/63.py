"""63. Unique Paths II (Medium).

Specification: https://leetcode.com/problems/unique-paths-ii/description/
"""


def solve(obstacleGrid: list[list[int]]) -> int:
    m, n = len(obstacleGrid), len(obstacleGrid[0])
    dp = [0] * n
    dp[0] = 1 if obstacleGrid[0][0] == 0 else 0
    for r in range(m):
        for c in range(n):
            if obstacleGrid[r][c] == 1:
                dp[c] = 0
            elif r == 0 and c == 0:
                continue
            elif c > 0:
                dp[c] += dp[c - 1]
    return dp[n - 1]


class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: list[list[int]]) -> int:
        return solve(obstacleGrid)
