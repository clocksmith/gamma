"""1254. Number of Closed Islands (Medium).

Specification: https://leetcode.com/problems/number-of-closed-islands/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    copy = [row[:] for row in grid]

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or copy[r][c] != 0:
            return
        copy[r][c] = 1
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    for r in range(rows):
        dfs(r, 0)
        dfs(r, cols - 1)
    for c in range(cols):
        dfs(0, c)
        dfs(rows - 1, c)
    count = 0
    for r in range(rows):
        for c in range(cols):
            if copy[r][c] == 0:
                count += 1
                dfs(r, c)
    return count


class Solution:
    def closedIsland(self, grid: list[list[int]]) -> int:
        return solve(grid)
