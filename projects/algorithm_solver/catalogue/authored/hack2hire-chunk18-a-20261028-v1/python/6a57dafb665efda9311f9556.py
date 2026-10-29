"""Hack2Hire 6a57dafb665efda9311f9556 (Maximum Grid Jumping Path, variant 4 of 4) over an INFERRED spec; qualification unknown."""


MOD = 1000000007


def solve(board, p, k):
    rows, cols = len(board), len(board[0])
    value = [[[None] * cols for _ in range(k + 1)] for _ in range(rows)]
    count = [[[0] * cols for _ in range(k + 1)] for _ in range(rows)]
    value[0][0][p] = board[0][p]
    count[0][0][p] = 1
    for i in range(1, rows):
        for u in range(k + 1):
            sources = [(i - 1, u, -1), (i - 1, u, 0), (i - 1, u, 1)]
            if i >= 2 and u >= 1:
                sources.append((i - 2, u - 1, 0))
            for j in range(cols):
                top, ways = None, 0
                for a, w, d in sources:
                    c = j + d
                    if 0 <= c < cols:
                        v = value[a][w][c]
                        if v is None:
                            continue
                        if top is None or v > top:
                            top, ways = v, count[a][w][c]
                        elif v == top:
                            ways = (ways + count[a][w][c]) % MOD
                if top is not None:
                    value[i][u][j] = top + board[i][j]
                    count[i][u][j] = ways
    top, ways = None, 0
    for u in range(k + 1):
        for j in range(cols):
            v = value[rows - 1][u][j]
            if v is None:
                continue
            if top is None or v > top:
                top, ways = v, count[rows - 1][u][j]
            elif v == top:
                ways = (ways + count[rows - 1][u][j]) % MOD
    return ways


class Solution:
    def countBestPaths(self, board, p, k):
        return solve(board, p, k)
