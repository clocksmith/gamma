"""1260. Shift 2D Grid (Easy).

Specification: https://leetcode.com/problems/shift-2d-grid/description/
"""


def solve(grid: list[list[int]], k: int) -> list[list[int]]:
    """O(m * n) time and result space; preserve grid and row identities."""
    rows, columns = len(grid), len(grid[0])
    size = rows * columns
    shift = k % size
    result = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        for column in range(columns):
            target = (row * columns + column + shift) % size
            result[target // columns][target % columns] = grid[row][column]
    return result


class Solution:
    def shiftGrid(self, grid: list[list[int]], k: int) -> list[list[int]]:
        return solve(grid, k)
