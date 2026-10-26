"""2639. Find the Width of Columns of a Grid (Easy).

Specification: https://leetcode.com/problems/find-the-width-of-columns-of-a-grid/description/
"""


def solve(grid: list[list[int]]) -> list[int]:
    """O(r * c * d) time, O(c + d) space; preserve grid; d is maximum digit width."""
    widths = [0] * len(grid[0])
    for row in grid:
        for column, value in enumerate(row):
            widths[column] = max(widths[column], len(str(value)))
    return widths


class Solution:
    def findColumnWidth(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
