"""2661. First Completely Painted Row or Column: map values to cells and count painted cells per row and column."""


def solve(arr: list[int], mat: list[list[int]]) -> int:
    """O(r * c) time and O(r * c) auxiliary space; inputs are read-only."""
    rows, columns = len(mat), len(mat[0])
    positions = [None] * (rows * columns + 1)
    for row in range(rows):
        for column in range(columns):
            positions[mat[row][column]] = (row, column)
    row_counts = [0] * rows
    column_counts = [0] * columns
    for index, value in enumerate(arr):
        row, column = positions[value]
        row_counts[row] += 1
        column_counts[column] += 1
        if row_counts[row] == columns or column_counts[column] == rows:
            return index
    return -1


class Solution:
    def firstCompleteIndex(self, arr: list[int], mat: list[list[int]]) -> int:
        return solve(arr, mat)
