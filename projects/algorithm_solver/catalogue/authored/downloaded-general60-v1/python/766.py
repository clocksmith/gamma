"""766. Toeplitz Matrix (Easy).

Specification: https://leetcode.com/problems/toeplitz-matrix/description/
"""


def solve(matrix: list[list[int]]) -> bool:
    for r in range(1, len(matrix)):
        for c in range(1, len(matrix[0])):
            if matrix[r][c] != matrix[r - 1][c - 1]:
                return False
    return True


class Solution:
    def isToeplitzMatrix(self, matrix: list[list[int]]) -> bool:
        return solve(matrix)
