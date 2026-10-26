"""1605. Find Valid Matrix Given Row and Column Sums: satisfy one residual row or column at every placement."""


def solve(rowSum: list[int], colSum: list[int]) -> list[list[int]]:
    """O(r * c + r + c) time and O(r + c) auxiliary space excluding the result; inputs are read-only."""
    rows, cols = len(rowSum), len(colSum)
    row_need, col_need = rowSum.copy(), colSum.copy()
    result = [[0] * cols for _ in range(rows)]
    row = col = 0
    while row < rows and col < cols:
        value = min(row_need[row], col_need[col])
        result[row][col] = value
        row_need[row] -= value
        col_need[col] -= value
        row_done = row_need[row] == 0
        col_done = col_need[col] == 0
        if row_done:
            row += 1
        if col_done:
            col += 1
    return result


class Solution:
    def restoreMatrix(self, rowSum: list[int], colSum: list[int]) -> list[list[int]]:
        return solve(rowSum, colSum)
