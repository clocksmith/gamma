"""695. Max Area of Island (Medium).

Specification: https://leetcode.com/problems/max-area-of-island/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    copy = [row[:] for row in grid]

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or copy[r][c] != 1:
            return 0
        copy[r][c] = 0
        return 1 + dfs(r + 1, c) + dfs(r - 1, c) + dfs(r, c + 1) + dfs(r, c - 1)

    best = 0
    for r in range(rows):
        for c in range(cols):
            if copy[r][c] == 1:
                best = max(best, dfs(r, c))
    return best


class Solution:
    def maxAreaOfIsland(self, grid: list[list[int]]) -> int:
        return solve(grid)
