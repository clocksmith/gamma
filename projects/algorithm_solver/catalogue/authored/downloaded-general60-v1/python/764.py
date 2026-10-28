"""764. Largest Plus Sign (Medium).

Specification: https://leetcode.com/problems/largest-plus-sign/description/
"""


def solve(n: int, mines: list[list[int]]) -> int:
    is_mine = {(r, c) for r, c in mines}
    dp = [[0] * n for _ in range(n)]
    for r in range(n):
        count = 0
        for c in range(n):
            count = 0 if (r, c) in is_mine else count + 1
            dp[r][c] = count
        count = 0
        for c in range(n - 1, -1, -1):
            count = 0 if (r, c) in is_mine else count + 1
            dp[r][c] = min(dp[r][c], count)
    best = 0
    for c in range(n):
        count = 0
        for r in range(n):
            count = 0 if (r, c) in is_mine else count + 1
            dp[r][c] = min(dp[r][c], count)
        count = 0
        for r in range(n - 1, -1, -1):
            count = 0 if (r, c) in is_mine else count + 1
            dp[r][c] = min(dp[r][c], count)
            best = max(best, dp[r][c])
    return best


class Solution:
    def orderOfLargestPlusSign(self, n: int, mines: list[list[int]]) -> int:
        return solve(n, mines)
