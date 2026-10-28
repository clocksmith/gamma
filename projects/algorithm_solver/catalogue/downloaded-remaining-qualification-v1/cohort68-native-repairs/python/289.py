"""289. Game of Life (Medium).

Specification: https://leetcode.com/problems/game-of-life/description/
"""


def solve(board: list[list[int]]) -> list[list[int]]:
    rows, cols = len(board), len(board[0])
    nxt = [row[:] for row in board]
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for r in range(rows):
        for c in range(cols):
            live = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    live += board[nr][nc]
            if board[r][c] == 1:
                nxt[r][c] = 1 if live in (2, 3) else 0
            else:
                nxt[r][c] = 1 if live == 3 else 0
    return nxt


class Solution:
    def gameOfLife(self, board: list[list[int]]) -> None:
        rows, cols = len(board), len(board[0])
        for r in range(rows):
            for c in range(cols):
                live = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr or dc:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                live += board[nr][nc] & 1
                if live == 3 or ((board[r][c] & 1) and live == 2):
                    board[r][c] |= 2
        for r in range(rows):
            for c in range(cols):
                board[r][c] >>= 1
