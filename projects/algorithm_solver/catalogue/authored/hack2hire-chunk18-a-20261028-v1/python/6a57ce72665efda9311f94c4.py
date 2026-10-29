"""Hack2Hire 6a57ce72665efda9311f94c4 (Maximum Grid Jumping Path, variant 1 of 4) over an INFERRED spec; qualification unknown."""


def solve(board, p):
    rows, cols = len(board), len(board[0])
    current = [None] * cols
    current[p] = board[0][p]
    for i in range(1, rows):
        nxt = [None] * cols
        row = board[i]
        for j in range(cols):
            best = None
            for c in (j - 1, j, j + 1):
                if 0 <= c < cols and current[c] is not None and (best is None or current[c] > best):
                    best = current[c]
            if best is not None:
                nxt[j] = best + row[j]
        current = nxt
    return max(v for v in current if v is not None)


class Solution:
    def maxPathScore(self, board, p):
        return solve(board, p)
