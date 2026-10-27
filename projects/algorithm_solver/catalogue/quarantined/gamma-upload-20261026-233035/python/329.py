"""329. Longest Increasing Path in a Matrix."""
from functools import lru_cache

def solve(matrix: list[list[int]]) -> int:
    rows, columns = len(matrix), len(matrix[0])
    @lru_cache(None)
    def visit(row: int, column: int) -> int:
        best = 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and matrix[nr][nc] > matrix[row][column]:
                best = max(best, 1 + visit(nr, nc))
        return best
    return max(visit(row, column) for row in range(rows) for column in range(columns))

class Solution:
    def longestIncreasingPath(self, matrix):
        return solve(matrix)
