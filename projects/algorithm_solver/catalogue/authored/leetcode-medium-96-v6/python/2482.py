"""2482. Difference Between Ones and Zeros in Row and Column: derive each output cell from its row and column one counts."""


def solve(grid: list[list[int]]) -> list[list[int]]:
    """O(mn) time and O(m + n) auxiliary space beyond the O(mn) result; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    row_ones = [0] * rows
    column_ones = [0] * columns
    for row in range(rows):
        for column in range(columns):
            row_ones[row] += grid[row][column]
            column_ones[column] += grid[row][column]
    return [[2 * (row_ones[row] + column_ones[column]) - rows - columns
             for column in range(columns)] for row in range(rows)]


class Solution:
    def onesMinusZeros(self, grid: list[list[int]]) -> list[list[int]]:
        return solve(grid)
