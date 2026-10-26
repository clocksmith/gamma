"""1582. Special Positions in a Binary Matrix (Easy).

Specification: https://leetcode.com/problems/special-positions-in-a-binary-matrix/description/
"""


def solve(mat: list[list[int]]) -> int:
    """O(m * n) time, O(m + n) space; preserve mat and its rows."""
    rows, columns = len(mat), len(mat[0])
    row_counts = [0] * rows
    column_counts = [0] * columns
    for row in range(rows):
        for column in range(columns):
            row_counts[row] += mat[row][column]
            column_counts[column] += mat[row][column]
    result = 0
    for row in range(rows):
        if row_counts[row] != 1:
            continue
        for column in range(columns):
            if mat[row][column] == 1 and column_counts[column] == 1:
                result += 1
    return result


class Solution:
    def numSpecial(self, mat: list[list[int]]) -> int:
        return solve(mat)
