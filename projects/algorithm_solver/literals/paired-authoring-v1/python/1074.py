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
    def numSubmatrixSumTarget(self, matrix: list[list[int]], target: int) -> int:
        rows = len(matrix)
        columns = len(matrix[0]) if rows > 0 else 0
        prefix = matrix_prefix(matrix)
        answer = 0
        for top in range(rows):
            for bottom in range(top + 1, rows + 1):
                frequencies = {0: 1}
                total = 0
                for column in range(columns):
                    total += rectangle_sum(prefix, top, column, bottom, column + 1)
                    answer += frequencies.get(total - target, 0)
                    frequencies[total] = frequencies.get(total, 0) + 1
        return answer
