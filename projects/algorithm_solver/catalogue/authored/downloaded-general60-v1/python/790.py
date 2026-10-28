"""790. Domino and Tromino Tiling (Medium).

Specification: https://leetcode.com/problems/domino-and-tromino-tiling/description/
"""


def solve(n: int) -> int:
    MOD = 1000000007
    if n == 1:
        return 1
    if n == 2:
        return 2
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    dp[2] = 2
    for i in range(3, n + 1):
        dp[i] = (2 * dp[i - 1] + dp[i - 3]) % MOD
    return dp[n]


class Solution:
    def numTilings(self, n: int) -> int:
        return solve(n)
