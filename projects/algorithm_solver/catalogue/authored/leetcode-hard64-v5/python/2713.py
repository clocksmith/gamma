"""2713. Maximum Strictly Increasing Cells in a Matrix. Batch equal values before updating row and column maxima."""


def solve(mat: list[list[int]]) -> int:
    """O(m*n log(m*n)) time and O(m*n) space. Inputs are preserved."""
    rows, columns = len(mat), len(mat[0])
    cells = sorted((mat[row][column], row, column) for row in range(rows) for column in range(columns))
    row_best = [0] * rows
    column_best = [0] * columns
    answer = 0
    begin = 0
    while begin < len(cells):
        end = begin
        updates = []
        while end < len(cells) and cells[end][0] == cells[begin][0]:
            _, row, column = cells[end]
            length = 1 + max(row_best[row], column_best[column])
            updates.append((row, column, length))
            answer = max(answer, length)
            end += 1
        for row, column, length in updates:
            row_best[row] = max(row_best[row], length)
            column_best[column] = max(column_best[column], length)
        begin = end
    return answer


class Solution:
    def maxIncreasingCells(self, mat: list[list[int]]) -> int:
        return solve(mat)
