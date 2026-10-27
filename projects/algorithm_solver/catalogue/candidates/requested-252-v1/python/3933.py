"""3933. Largest Local Values in a Matrix II.

Specification: https://leetcode.com/problems/largest-local-values-in-a-matrix-ii/description/
"""

from __future__ import annotations


def solve(matrix: list[list[int]]) -> int:
    """O(V*rows*columns) time and O(rows*columns) space, at most 200 distinct positive values. Inputs are preserved."""
    rows, columns = len(matrix), len(matrix[0])
    groups = {}
    for row in range(rows):
        for column in range(columns):
            value = matrix[row][column]
            if value:
                groups.setdefault(value, []).append((row, column))
    answer = 0
    for value, cells in groups.items():
        prefix = [[0] * (columns + 1) for _ in range(rows + 1)]
        for row in range(rows):
            running = 0
            for column in range(columns):
                running += matrix[row][column] > value
                prefix[row + 1][column + 1] = prefix[row][column + 1] + running
        for row, column in cells:
            top, bottom = max(0, row - value), min(rows - 1, row + value)
            left, right = max(0, column - value), min(columns - 1, column + value)
            larger = (prefix[bottom + 1][right + 1] - prefix[top][right + 1]
                      - prefix[bottom + 1][left] + prefix[top][left])
            for r in (row - value, row + value):
                for c in (column - value, column + value):
                    if 0 <= r < rows and 0 <= c < columns and matrix[r][c] > value:
                        larger -= 1
            answer += larger == 0
    return answer
