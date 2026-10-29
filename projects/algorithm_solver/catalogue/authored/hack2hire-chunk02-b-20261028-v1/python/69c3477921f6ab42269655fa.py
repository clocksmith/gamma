"""Original Hack2Hire 69c3477921f6ab42269655fa variant over an INFERRED specification; qualification unknown."""

DIRECTIONS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def solve(board, row, col, player):
    n = len(board)
    out = [list(line) for line in board]
    if board[row][col] != '.':
        return out
    flips = []
    for dr, dc in DIRECTIONS:
        r, c, run = row + dr, col + dc, []
        while 0 <= r < n and 0 <= c < n and board[r][c] not in ('.', player):
            run.append((r, c))
            r, c = r + dr, c + dc
        if run and 0 <= r < n and 0 <= c < n and board[r][c] == player:
            flips.extend(run)
    if flips:
        out[row][col] = player
        for r, c in flips:
            out[r][c] = player
    return out


class Solution:
    def reversiMove(self, board, row, col, player):
        return solve(board, row, col, player)
