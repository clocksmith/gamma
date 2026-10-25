"""1351. Count Negative Numbers in a Sorted Matrix (Easy).

Specification: https://leetcode.com/problems/count-negative-numbers-in-a-sorted-matrix/description/
"""


def solve(grid: list[list[int]]) -> int:
    """O(rows + columns) time, O(1) auxiliary space; preserve all inputs."""
    columns = len(grid[0])
    row = len(grid) - 1
    column = 0
    count = 0
    while row >= 0 and column < columns:
        if grid[row][column] < 0:
            count += columns - column
            row -= 1
        else:
            column += 1
    return count


class Solution:
    def countNegatives(self, grid: list[list[int]]) -> int:
        return solve(grid)
