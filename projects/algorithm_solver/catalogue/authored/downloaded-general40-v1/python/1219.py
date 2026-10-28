"""1219. Path with Maximum Gold (Medium).

Specification: https://leetcode.com/problems/path-with-maximum-gold/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    best = 0

    def dfs(r, c, total):
        nonlocal best
        best = max(best, total)
        saved = grid[r][c]
        grid[r][c] = 0
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] > 0:
                dfs(nr, nc, total + grid[nr][nc])
        grid[r][c] = saved

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] > 0:
                dfs(r, c, grid[r][c])
    return best


class Solution:
    def getMaximumGold(self, grid: list[list[int]]) -> int:
        return solve(grid)
