"""Original frontend 1246 variant; qualification unknown."""


def solve(arr) -> int:
    n = len(arr)
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            best = 1 + dp[i + 1][j]
            if arr[i] == arr[i + 1]:
                cand = 1 + (dp[i + 2][j] if i + 2 <= j else 0)
                if cand < best:
                    best = cand
            ai = arr[i]
            for k in range(i + 2, j + 1):
                if ai == arr[k]:
                    cand = dp[i + 1][k - 1] + (dp[k + 1][j] if k + 1 <= j else 0)
                    if cand < best:
                        best = cand
            dp[i][j] = best
    return dp[0][n - 1]


minimumMoves = solve


class Solution:
    def minimumMoves(self, arr) -> int:
        return solve(arr)
