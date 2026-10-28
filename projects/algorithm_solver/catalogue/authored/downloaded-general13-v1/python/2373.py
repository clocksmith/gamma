"""2373. Largest Local Values in a Matrix (Easy).

Specification: https://leetcode.com/problems/largest-local-values-in-a-matrix/description/
"""


def solve(grid):
    n = len(grid)
    out = []
    for i in range(n - 2):
        row = []
        for j in range(n - 2):
            best = max(grid[i + di][j + dj] for di in range(3) for dj in range(3))
            row.append(best)
        out.append(row)
    return out


class Solution:
    def largestLocal(self, grid):
        return solve(grid)
