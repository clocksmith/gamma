"""Hack2Hire 6a57d29e665efda9311f950a (Maximum Grid Jumping Path, variant 2 of 4) over an INFERRED spec; qualification unknown."""


def solve(board, p, k):
    rows, cols = len(board), len(board[0])
    # best[i][u][j]: largest sum reaching (i, j) with exactly u jumps; None when unreachable
    best = [[[None] * cols for _ in range(k + 1)] for _ in range(rows)]
    best[0][0][p] = board[0][p]
    for i in range(1, rows):
        row = board[i]
        for u in range(k + 1):
            above = best[i - 1][u]
            jump = best[i - 2][u - 1] if i >= 2 and u >= 1 else None
            target = best[i][u]
            for j in range(cols):
                top = None
                for c in (j - 1, j, j + 1):
                    if 0 <= c < cols and above[c] is not None and (top is None or above[c] > top):
                        top = above[c]
                if jump is not None and jump[j] is not None and (top is None or jump[j] > top):
                    top = jump[j]
                if top is not None:
                    target[j] = top + row[j]
    return max(v for layer in best[rows - 1] for v in layer if v is not None)


class Solution:
    def maxPathScoreWithJumps(self, board, p, k):
        return solve(board, p, k)
