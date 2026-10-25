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
    def largest1BorderedSquare(self, grid: list[list[int]]) -> int:
        rows = len(grid)
        columns = len(grid[0]) if rows > 0 else 0
        prefix = matrix_prefix(grid)
        for side in range(min(rows, columns), 0, -1):
            required = 1 if side == 1 else 4 * side - 4
            for top in range(rows - side + 1):
                for left in range(columns - side + 1):
                    bottom = top + side
                    right = left + side
                    border = rectangle_sum(prefix, top, left, bottom, right)
                    if side > 2:
                        border -= rectangle_sum(prefix, top + 1, left + 1, bottom - 1, right - 1)
                    if border == required:
                        return side * side
        return 0
