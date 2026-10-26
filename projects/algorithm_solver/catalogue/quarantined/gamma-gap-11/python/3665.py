"""3665. Twisted Mirror Path Count."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> int:
    """O(rows * columns) time and O(columns) auxiliary space; inputs are preserved."""
    modulus = 1_000_000_007
    columns = len(grid[0])
    down = [0] * columns
    down[0] = 1
    for row in grid:
        right = 0
        for column, mirror in enumerate(row):
            above = down[column]
            if mirror:
                down[column], right = right, above
            else:
                ways = (above + right) % modulus
                down[column] = right = ways
    return down[-1]


class Solution:
    def uniquePaths(self, grid: list[list[int]]) -> int:
        return solve(grid)
