"""2556. Disconnect Path in a Binary Matrix by at Most One Flip (Medium).

Specification: https://leetcode.com/problems/disconnect-path-in-a-binary-matrix-by-at-most-one-flip/description/
"""


def solve(grid):
    g = [row[:] for row in grid]
    m, n = len(g), len(g[0])

    def dfs(i, j):
        if i >= m or j >= n or g[i][j] != 1:
            return False
        if i == m - 1 and j == n - 1:
            return True
        g[i][j] = 0
        return dfs(i + 1, j) or dfs(i, j + 1)

    a = dfs(0, 0)
    g[0][0] = 1
    g[m - 1][n - 1] = 1
    b = dfs(0, 0)
    return not (a and b)


class Solution:
    def isPossibleToCutPath(self, grid):
        return solve(grid)
