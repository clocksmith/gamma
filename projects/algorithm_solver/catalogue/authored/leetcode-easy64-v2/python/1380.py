"""1380. Lucky Numbers in a Matrix (Easy).

Specification: https://leetcode.com/problems/lucky-numbers-in-a-matrix/description/
"""


def solve(matrix: list[list[int]]) -> list[int]:
    """O(rows * columns) time, O(rows + columns) auxiliary space; preserve matrix."""
    rows, columns = len(matrix), len(matrix[0])
    row_minima = [min(row) for row in matrix]
    column_maxima = [max(matrix[row][column] for row in range(rows))
                     for column in range(columns)]
    result = []
    for row in range(rows):
        for column in range(columns):
            value = matrix[row][column]
            if value == row_minima[row] and value == column_maxima[column]:
                result.append(value)
    return result


class Solution:
    def luckyNumbers(self, matrix: list[list[int]]) -> list[int]:
        return solve(matrix)
