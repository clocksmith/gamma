"""688. Knight Probability in Chessboard (Medium).

Specification: https://leetcode.com/problems/knight-probability-in-chessboard/description/
"""


def solve(n: int, k: int, row: int, column: int) -> float:
    dp = [[0.0] * n for _ in range(n)]
    dp[row][column] = 1.0
    moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for _step in range(k):
        nxt = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                if dp[r][c] == 0:
                    continue
                for dr, dc in moves:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        nxt[nr][nc] += dp[r][c] / 8
        dp = nxt
    return sum(sum(row_values) for row_values in dp)


class Solution:
    def knightProbability(self, n: int, k: int, row: int, column: int) -> float:
        return solve(n, k, row, column)
