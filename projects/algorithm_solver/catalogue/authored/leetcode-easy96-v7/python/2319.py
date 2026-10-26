"""2319. Check if Matrix Is X-Matrix (Easy).

Specification: https://leetcode.com/problems/check-if-matrix-is-x-matrix/description/
"""


def solve(grid: list[list[int]]) -> bool:
    """O(n^2) time, O(1) space; exactly the two diagonals must be nonzero; preserve grid."""
    size = len(grid)
    for row in range(size):
        for column in range(size):
            diagonal = row == column or row + column == size - 1
            if (grid[row][column] != 0) != diagonal:
                return False
    return True


class Solution:
    def checkXMatrix(self, grid: list[list[int]]) -> bool:
        return solve(grid)
