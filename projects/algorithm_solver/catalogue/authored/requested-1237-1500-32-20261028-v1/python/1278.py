"""Original frontend 1278 variant; qualification unknown."""


def solve(s: str, k: int) -> int:
    n = len(s)
    cost = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            cost[i][j] = cost[i + 1][j - 1] + (0 if s[i] == s[j] else 1)
    dp = [cost[0][i] for i in range(n)]
    for parts in range(2, k + 1):
        nxt = [n] * n
        for i in range(parts - 1, n):
            best = n
            for p in range(parts - 2, i):
                v = dp[p] + cost[p + 1][i]
                if v < best:
                    best = v
            nxt[i] = best
        dp = nxt
    return dp[n - 1]


palindromePartition = solve


class Solution:
    def palindromePartition(self, s: str, k: int) -> int:
        return solve(s, k)
