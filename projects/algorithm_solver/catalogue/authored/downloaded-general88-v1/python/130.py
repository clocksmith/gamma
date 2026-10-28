"""130. Surrounded Regions (Medium).

Specification: https://leetcode.com/problems/surrounded-regions/description/
"""


def solve(board: list[list[str]]) -> list[list[str]]:
    rows, cols = len(board), len(board[0])
    result = [row[:] for row in board]

    def mark(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or result[r][c] != 'O':
            return
        result[r][c] = 'S'
        mark(r + 1, c)
        mark(r - 1, c)
        mark(r, c + 1)
        mark(r, c - 1)

    for r in range(rows):
        mark(r, 0)
        mark(r, cols - 1)
    for c in range(cols):
        mark(0, c)
        mark(rows - 1, c)
    for r in range(rows):
        for c in range(cols):
            if result[r][c] == 'O':
                result[r][c] = 'X'
            elif result[r][c] == 'S':
                result[r][c] = 'O'
    return result


class Solution:
    def solve(self, board: list[list[str]]) -> list[list[str]]:
        return solve(board)
