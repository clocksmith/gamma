"""3393. Count Paths With the Given XOR Value (Medium).

Specification: https://leetcode.com/problems/count-paths-with-the-given-xor-value/description/
"""


def solve(grid: list[list[int]], k: int) -> int:
    MOD = 1000000007
    m = len(grid)
    n = len(grid[0])
    dp = [[[0] * 16 for _ in range(n)] for _ in range(m)]
    dp[0][0][grid[0][0]] = 1
    for i in range(m):
        for j in range(n):
            for v in range(16):
                ways = dp[i][j][v]
                if not ways:
                    continue
                if i + 1 < m:
                    nv = v ^ grid[i + 1][j]
                    dp[i + 1][j][nv] = (dp[i + 1][j][nv] + ways) % MOD
                if j + 1 < n:
                    nv = v ^ grid[i][j + 1]
                    dp[i][j + 1][nv] = (dp[i][j + 1][nv] + ways) % MOD
    return dp[m - 1][n - 1][k]


class Solution:
    def countPaths(self, grid: list[list[int]], k: int) -> int:
        return solve(grid, k)
