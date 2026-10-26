"""3033. Modify the Matrix (Easy).

Specification: https://leetcode.com/problems/modify-the-matrix/description/
"""


def solve(matrix: list[list[int]]) -> list[list[int]]:
    """O(rows * columns) time and output space; return fresh rows and preserve matrix."""
    result = [row.copy() for row in matrix]
    for column in range(len(matrix[0])):
        maximum = -1
        for row in range(len(matrix)):
            maximum = max(maximum, matrix[row][column])
        for row in range(len(matrix)):
            if result[row][column] == -1:
                result[row][column] = maximum
    return result


class Solution:
    def modifiedMatrix(self, matrix: list[list[int]]) -> list[list[int]]:
        return solve(matrix)
