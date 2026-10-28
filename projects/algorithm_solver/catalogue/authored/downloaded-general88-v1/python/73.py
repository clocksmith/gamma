"""73. Set Matrix Zeroes (Medium).

Specification: https://leetcode.com/problems/set-matrix-zeroes/description/
"""


def solve(matrix: list[list[int]]) -> list[list[int]]:
    rows, cols = len(matrix), len(matrix[0])
    zero_rows = set()
    zero_cols = set()
    for r in range(rows):
        for c in range(cols):
            if matrix[r][c] == 0:
                zero_rows.add(r)
                zero_cols.add(c)
    result = [row[:] for row in matrix]
    for r in range(rows):
        for c in range(cols):
            if r in zero_rows or c in zero_cols:
                result[r][c] = 0
    return result


class Solution:
    def setZeroes(self, matrix: list[list[int]]) -> list[list[int]]:
        return solve(matrix)
