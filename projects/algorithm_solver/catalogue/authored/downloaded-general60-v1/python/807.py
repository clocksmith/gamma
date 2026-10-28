"""807. Max Increase to Keep City Skyline (Medium).

Specification: https://leetcode.com/problems/max-increase-to-keep-city-skyline/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    row_max = [max(row) for row in grid]
    col_max = [max(grid[r][c] for r in range(rows)) for c in range(cols)]
    total = 0
    for r in range(rows):
        for c in range(cols):
            total += min(row_max[r], col_max[c]) - grid[r][c]
    return total


class Solution:
    def maxIncreaseKeepingSkyline(self, grid: list[list[int]]) -> int:
        return solve(grid)
