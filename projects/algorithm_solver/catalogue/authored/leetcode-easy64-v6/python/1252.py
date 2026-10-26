"""1252. Cells with Odd Values in a Matrix (Easy).

Specification: https://leetcode.com/problems/cells-with-odd-values-in-a-matrix/description/
"""


def solve(m: int, n: int, indices: list[list[int]]) -> int:
    """O(m + n + q) time, O(m + n) space; q = len(indices); preserve inputs."""
    rows = [False] * m
    columns = [False] * n
    for row, column in indices:
        rows[row] = not rows[row]
        columns[column] = not columns[column]
    odd_rows = sum(rows)
    odd_columns = sum(columns)
    return odd_rows * (n - odd_columns) + (m - odd_rows) * odd_columns


class Solution:
    def oddCells(self, m: int, n: int, indices: list[list[int]]) -> int:
        return solve(m, n, indices)
