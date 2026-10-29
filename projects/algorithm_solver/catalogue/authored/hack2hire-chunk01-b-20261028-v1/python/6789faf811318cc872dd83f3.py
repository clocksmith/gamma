"""Hack2Hire 6789faf811318cc872dd83f3 (Find Robots Position). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown."""


def solve(board, distances):
    rows, cols = len(board), len(board[0])
    left = [[0] * cols for _ in range(rows)]
    right = [[0] * cols for _ in range(rows)]
    for r in range(rows):
        row, blocker = board[r], -1
        for c in range(cols):
            if row[c] == 'X':
                blocker = c
            else:
                left[r][c] = c - blocker
        blocker = cols
        for c in range(cols - 1, -1, -1):
            if row[c] == 'X':
                blocker = c
            else:
                right[r][c] = blocker - c
    top = [[0] * cols for _ in range(rows)]
    bottom = [[0] * cols for _ in range(rows)]
    for c in range(cols):
        blocker = -1
        for r in range(rows):
            if board[r][c] == 'X':
                blocker = r
            else:
                top[r][c] = r - blocker
        blocker = rows
        for r in range(rows - 1, -1, -1):
            if board[r][c] == 'X':
                blocker = r
            else:
                bottom[r][c] = blocker - r
    want_left, want_top, want_bottom, want_right = distances
    return [[r, c] for r in range(rows) for c in range(cols)
            if board[r][c] == 'O' and left[r][c] == want_left and top[r][c] == want_top
            and bottom[r][c] == want_bottom and right[r][c] == want_right]


class Solution:
    def findRobotPositions(self, board, distances):
        return solve(board, distances)
