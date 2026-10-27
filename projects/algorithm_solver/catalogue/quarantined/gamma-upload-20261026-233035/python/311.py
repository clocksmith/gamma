"""311. Sparse Matrix Multiplication."""
def solve(mat1: list[list[int]], mat2: list[list[int]]) -> list[list[int]]:
    rows, inner, columns = len(mat1), len(mat2), len(mat2[0])
    nonzero = [[(column, value) for column, value in enumerate(row) if value] for row in mat2]
    result = [[0] * columns for _ in range(rows)]
    for row in range(rows):
        for index in range(inner):
            if mat1[row][index]:
                for column, value in nonzero[index]:
                    result[row][column] += mat1[row][index] * value
    return result

class Solution:
    def multiply(self, mat1, mat2):
        return solve(mat1, mat2)
