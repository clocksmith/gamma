"""1594. Maximum Non Negative Product in a Matrix (Medium).

Specification: https://leetcode.com/problems/maximum-non-negative-product-in-a-matrix/description/
"""


def solve(grid: list[list[int]]) -> int:
    MOD = 1000000007
    rows, cols = len(grid), len(grid[0])
    min_dp = [[0] * cols for _ in range(rows)]
    max_dp = [[0] * cols for _ in range(rows)]
    min_dp[0][0] = grid[0][0]
    max_dp[0][0] = grid[0][0]
    for r in range(rows):
        for c in range(cols):
            if r == 0 and c == 0:
                continue
            candidates = []
            if r > 0:
                candidates.append(min_dp[r - 1][c] * grid[r][c])
                candidates.append(max_dp[r - 1][c] * grid[r][c])
            if c > 0:
                candidates.append(min_dp[r][c - 1] * grid[r][c])
                candidates.append(max_dp[r][c - 1] * grid[r][c])
            min_dp[r][c] = min(candidates)
            max_dp[r][c] = max(candidates)
    best = max_dp[rows - 1][cols - 1]
    return -1 if best < 0 else best % MOD


class Solution:
    def maxProductPath(self, grid: list[list[int]]) -> int:
        return solve(grid)
