"""200. Number of Islands (Medium).

Specification: https://leetcode.com/problems/number-of-islands/description/
"""


def solve(grid: list[list[str]]) -> int:
    rows, cols = len(grid), len(grid[0])
    copy = [row[:] for row in grid]

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or copy[r][c] != '1':
            return
        copy[r][c] = '0'
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if copy[r][c] == '1':
                count += 1
                dfs(r, c)
    return count


class Solution:
    def numIslands(self, grid: list[list[str]]) -> int:
        return solve(grid)
