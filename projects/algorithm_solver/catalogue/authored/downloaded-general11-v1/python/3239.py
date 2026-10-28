"""3239. Minimum Number of Flips to Make Binary Grid Palindromic I (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-flips-to-make-binary-grid-palindromic-i/description/
"""


def solve(grid: list[list[int]]) -> int:
    m, n = len(grid), len(grid[0])
    rows = 0
    cols = 0
    for i in range(m):
        for j in range(n // 2):
            if grid[i][j] != grid[i][n - 1 - j]:
                rows += 1
    for j in range(n):
        for i in range(m // 2):
            if grid[i][j] != grid[m - 1 - i][j]:
                cols += 1
    return min(rows, cols)


class Solution:
    def minFlips(self, grid):
        return solve(grid)
