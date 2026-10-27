"""688. Knight Probability in Chessboard."""

def solve(n: int, k: int, row: int, column: int) -> float:
    moves = ((1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1))
    probability = [[0.0] * n for _ in range(n)]
    probability[row][column] = 1.0
    for _ in range(k):
        following = [[0.0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                if probability[r][c] == 0:
                    continue
                share = probability[r][c] / 8
                for dr, dc in moves:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < n and 0 <= nc < n:
                        following[nr][nc] += share
        probability = following
    return sum(map(sum, probability))


class Solution:
    def knightProbability(self, n: int, k: int, row: int, column: int) -> float:
        return solve(n, k, row, column)
