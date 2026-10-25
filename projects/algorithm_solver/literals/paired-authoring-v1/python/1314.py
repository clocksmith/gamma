def matrix_prefix(matrix: list[list[int]]) -> list[list[int]]:
    rows = len(matrix)
    columns = len(matrix[0]) if rows > 0 else 0
    prefix = [[0] * (columns + 1) for _ in range(rows + 1)]
    for row in range(rows):
        row_total = 0
        for column in range(columns):
            row_total += matrix[row][column]
            prefix[row + 1][column + 1] = prefix[row][column + 1] + row_total
    return prefix


def rectangle_sum(prefix: list[list[int]], top: int, left: int, bottom: int, right: int) -> int:
    return prefix[bottom][right] - prefix[top][right] - prefix[bottom][left] + prefix[top][left]


class Solution:
    def matrixBlockSum(self, mat: list[list[int]], k: int) -> list[list[int]]:
        rows = len(mat)
        columns = len(mat[0]) if rows > 0 else 0
        prefix = matrix_prefix(mat)
        output = [[0] * columns for _ in range(rows)]
        for row in range(rows):
            for column in range(columns):
                top = max(0, row - k)
                left = max(0, column - k)
                bottom = min(rows, row + k + 1)
                right = min(columns, column + k + 1)
                output[row][column] = rectangle_sum(prefix, top, left, bottom, right)
        return output
