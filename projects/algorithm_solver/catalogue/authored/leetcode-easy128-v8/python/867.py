"""867. Transpose Matrix (Easy).

Specification: https://leetcode.com/problems/transpose-matrix/description/
"""


def solve(matrix: list[list[int]]) -> list[list[int]]:
    """O(m * n) time and space; allocate independent rows for the transposed result."""
    rows, columns = len(matrix), len(matrix[0])
    result = [[0] * rows for _ in range(columns)]
    for row in range(rows):
        for column in range(columns):
            result[column][row] = matrix[row][column]
    return result


class Solution:
    def transpose(self, matrix: list[list[int]]) -> list[list[int]]:
        return solve(matrix)
