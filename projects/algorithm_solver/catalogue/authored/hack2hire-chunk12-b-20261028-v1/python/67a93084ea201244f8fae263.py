"""Hack2Hire 67a93084ea201244f8fae263 (Minimum Flips for Grid Symmetry) over an INFERRED spec; qualification unknown."""


def solve(grid):
    n, m = len(grid), len(grid[0])
    flips = 0
    for i in range((n + 1) // 2):
        rows = (i,) if i == n - 1 - i else (i, n - 1 - i)
        for j in range((m + 1) // 2):
            cols = (j,) if j == m - 1 - j else (j, m - 1 - j)
            size = len(rows) * len(cols)
            black = sum(1 for r in rows for c in cols if grid[r][c] == 'B')
            flips += min(black, size - black)
    return flips


class Solution:
    def minFlips(self, grid):
        return solve(grid)
