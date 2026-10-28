"""3142. Check if Grid Satisfies Conditions (Easy).

Specification: https://leetcode.com/problems/check-if-grid-satisfies-conditions/description/
"""


def solve(grid: list[list[int]]) -> bool:
    m, n = len(grid), len(grid[0])
    for i in range(m):
        for j in range(n):
            if i + 1 < m and grid[i][j] != grid[i + 1][j]:
                return False
            if j + 1 < n and grid[i][j] == grid[i][j + 1]:
                return False
    return True


class Solution:
    def satisfiesConditions(self, grid):
        return solve(grid)
