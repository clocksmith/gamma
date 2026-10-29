"""Hack2Hire 6a57d9ca665efda9311f954c (Maximum Grid Jumping Path, variant 3 of 4) over an INFERRED spec; qualification unknown."""


def solve(board, p, k):
    rows, cols = len(board), len(board[0])
    # down[i][r][j]: best sum from (i, j), counting it, to the bottom row with at most r jumps left
    down = [None] * rows
    down[rows - 1] = [list(board[rows - 1]) for _ in range(k + 1)]
    for i in range(rows - 2, -1, -1):
        row = board[i]
        layer = []
        for r in range(k + 1):
            below = down[i + 1][r]
            far = down[i + 2][r - 1] if r >= 1 and i + 2 <= rows - 1 else None
            values = []
            for j in range(cols):
                top = below[j]
                if j > 0 and below[j - 1] > top:
                    top = below[j - 1]
                if j + 1 < cols and below[j + 1] > top:
                    top = below[j + 1]
                if far is not None and far[j] > top:
                    top = far[j]
                values.append(top + row[j])
            layer.append(values)
        down[i] = layer
    path = [[0, p]]
    i, j, r = 0, p, k
    while i < rows - 1:
        need = down[i][r][j] - board[i][j]
        moves = [(i + 1, j - 1, r), (i + 1, j, r), (i + 1, j + 1, r)]
        if r >= 1 and i + 2 <= rows - 1:
            moves.append((i + 2, j, r - 1))
        for a, b, left in moves:
            if 0 <= b < cols and down[a][left][b] == need:
                i, j, r = a, b, left
                break
        path.append([i, j])
    return path


class Solution:
    def bestPathWithJumps(self, board, p, k):
        return solve(board, p, k)
