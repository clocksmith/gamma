"""221. Maximal Square (Medium).

Specification: https://leetcode.com/problems/maximal-square/description/
"""


def solve(matrix: list[list[str]]) -> int:
    if not matrix:
        return 0
    rows, cols = len(matrix), len(matrix[0])
    dp = [[0] * (cols + 1) for _ in range(rows + 1)]
    best = 0
    for r in range(rows):
        for c in range(cols):
            if matrix[r][c] == '1':
                dp[r + 1][c + 1] = 1 + min(dp[r][c], dp[r + 1][c], dp[r][c + 1])
                best = max(best, dp[r + 1][c + 1])
    return best * best


class Solution:
    def maximalSquare(self, matrix: list[list[str]]) -> int:
        return solve(matrix)
