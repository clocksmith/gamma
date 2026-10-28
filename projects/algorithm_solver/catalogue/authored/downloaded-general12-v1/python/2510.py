"""2510. Check if There is a Path With Equal Number of 0's And 1's (Medium).

Specification: https://leetcode.com/problems/check-if-there-is-a-path-with-equal-number-of-0-s-and-1-s/description/
"""


def solve(grid):
    m, n = len(grid), len(grid[0])
    total = m + n - 1
    if total % 2 != 0:
        return False
    target = total // 2
    dp = [[set() for _ in range(n)] for _ in range(m)]
    dp[0][0].add(grid[0][0])
    for i in range(m):
        for j in range(n):
            if i == 0 and j == 0:
                continue
            s = set()
            if i > 0:
                for c in dp[i - 1][j]:
                    nc = c + grid[i][j]
                    if nc <= target:
                        s.add(nc)
            if j > 0:
                for c in dp[i][j - 1]:
                    nc = c + grid[i][j]
                    if nc <= target:
                        s.add(nc)
            dp[i][j] = s
    return target in dp[m - 1][n - 1]


class Solution:
    def isThereAPath(self, grid):
        return solve(grid)
