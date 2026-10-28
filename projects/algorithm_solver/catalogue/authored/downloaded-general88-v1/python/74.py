"""74. Search a 2D Matrix (Medium).

Specification: https://leetcode.com/problems/search-a-2d-matrix/description/
"""


def solve(matrix: list[list[int]], target: int) -> bool:
    rows, cols = len(matrix), len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = (left + right) // 2
        value = matrix[mid // cols][mid % cols]
        if value == target:
            return True
        if value < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


class Solution:
    def searchMatrix(self, matrix: list[list[int]], target: int) -> bool:
        return solve(matrix, target)
