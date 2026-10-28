"""1034. Coloring A Border (Medium).

Specification: https://leetcode.com/problems/coloring-a-border/description/
"""


def solve(grid: list[list[int]], row: int, col: int, color: int) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    original = grid[row][col]
    result = [line[:] for line in grid]
    visited = set()

    def dfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != original or (r, c) in visited:
            return
        visited.add((r, c))
        is_border = (r == 0 or r == rows - 1 or c == 0 or c == cols - 1 or grid[r - 1][c] != original or grid[r + 1][c] != original or grid[r][c - 1] != original or grid[r][c + 1] != original)
        if is_border:
            result[r][c] = color
        dfs(r + 1, c)
        dfs(r - 1, c)
        dfs(r, c + 1)
        dfs(r, c - 1)

    dfs(row, col)
    return result


class Solution:
    def colorBorder(self, grid: list[list[int]], row: int, col: int, color: int) -> list[list[int]]:
        return solve(grid, row, col, color)
