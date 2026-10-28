"""1690. Stone Game VII (Medium).

Specification: https://leetcode.com/problems/stone-game-vii/description/
"""


def solve(stones: list[int]) -> int:
    n = len(stones)
    prefix = [0]
    for value in stones:
        prefix.append(prefix[-1] + value)

    def total(l, r):
        return prefix[r + 1] - prefix[l]

    dp = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for l in range(n - length + 1):
            r = l + length - 1
            dp[l][r] = max(total(l + 1, r) - dp[l + 1][r], total(l, r - 1) - dp[l][r - 1])
    return dp[0][n - 1]


class Solution:
    def stoneGameVII(self, stones: list[int]) -> int:
        return solve(stones)
