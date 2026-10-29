"""Original frontend 1692 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(n: int, k: int) -> int:
    dp = [0] * (k + 1)
    dp[0] = 1
    for _ in range(1, n + 1):
        for j in range(k, 0, -1):
            dp[j] = (dp[j] * j + dp[j - 1]) % MOD
        dp[0] = 0
    return dp[k]


waysToDistribute = solve


class Solution:
    def waysToDistribute(self, n: int, k: int) -> int:
        return solve(n, k)
