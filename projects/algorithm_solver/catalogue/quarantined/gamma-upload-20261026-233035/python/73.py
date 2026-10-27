"""73. Set Matrix Zeroes."""
def solve(matrix: list[list[int]]) -> None:
    first_row = any(value == 0 for value in matrix[0])
    first_column = any(row[0] == 0 for row in matrix)
    for row in range(1, len(matrix)):
        for column in range(1, len(matrix[0])):
            if matrix[row][column] == 0:
                matrix[row][0] = matrix[0][column] = 0
    for row in range(1, len(matrix)):
        for column in range(1, len(matrix[0])):
            if matrix[row][0] == 0 or matrix[0][column] == 0:
                matrix[row][column] = 0
    if first_row:
        matrix[0][:] = [0] * len(matrix[0])
    if first_column:
        for row in matrix:
            row[0] = 0

class Solution:
    def setZeroes(self, matrix: list[list[int]]) -> None:
        solve(matrix)
