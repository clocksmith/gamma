"""463. Island Perimeter (Easy).

Specification: https://leetcode.com/problems/island-perimeter/description/
"""


def solve(grid: list[list[int]]) -> int:
    """O(rows * columns) time, O(1) space; subtract shared edges once; preserve grid and rows."""
    perimeter = 0
    for row, cells in enumerate(grid):
        for column, value in enumerate(cells):
            if value != 1:
                continue
            perimeter += 4
            if row > 0 and grid[row - 1][column] == 1:
                perimeter -= 2
            if column > 0 and grid[row][column - 1] == 1:
                perimeter -= 2
    return perimeter


class Solution:
    def islandPerimeter(self, grid: list[list[int]]) -> int:
        return solve(grid)
