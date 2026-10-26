"""3402. Minimum Operations to Make Columns Strictly Increasing (Easy).

Specification: https://leetcode.com/problems/minimum-operations-to-make-columns-strictly-increasing/description/
"""


def solve(grid: list[list[int]]) -> int:
    """O(rows * columns) time, O(1) space; track adjusted heights without modifying grid."""
    operations = 0
    for column in range(len(grid[0])):
        previous = grid[0][column]
        for row in range(1, len(grid)):
            adjusted = max(grid[row][column], previous + 1)
            operations += adjusted - grid[row][column]
            previous = adjusted
    return operations


class Solution:
    def minimumOperations(self, grid: list[list[int]]) -> int:
        return solve(grid)
