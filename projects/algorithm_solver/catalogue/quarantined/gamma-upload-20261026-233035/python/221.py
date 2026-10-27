"""221. Maximal Square."""
def solve(matrix: list[list[str]]) -> int:
    columns = len(matrix[0])
    dp = [0] * (columns + 1)
    best = 0
    for row in matrix:
        diagonal = 0
        for column in range(1, columns + 1):
            above = dp[column]
            if row[column - 1] == '1':
                dp[column] = 1 + min(dp[column], dp[column - 1], diagonal)
                best = max(best, dp[column])
            else:
                dp[column] = 0
            diagonal = above
    return best * best

class Solution:
    def maximalSquare(self, matrix: list[list[str]]) -> int:
        return solve(matrix)
