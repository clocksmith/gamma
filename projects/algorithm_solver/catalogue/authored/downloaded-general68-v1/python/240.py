"""240. Search a 2D Matrix II (Medium).

Specification: https://leetcode.com/problems/search-a-2d-matrix-ii/description/
"""


def solve(matrix: list[list[int]], target: int) -> bool:
    if not matrix:
        return False
    row, col = 0, len(matrix[0]) - 1
    while row < len(matrix) and col >= 0:
        value = matrix[row][col]
        if value == target:
            return True
        if value > target:
            col -= 1
        else:
            row += 1
    return False


class Solution:
    def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:
        return solve(matrix, target)
