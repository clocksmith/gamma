"""694. Number of Distinct Islands (Medium).

Specification: https://leetcode.com/problems/number-of-distinct-islands/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    copy = [row[:] for row in grid]
    shapes = set()

    def dfs(r, c, base_r, base_c, cells):
        if r < 0 or r >= rows or c < 0 or c >= cols or copy[r][c] != 1:
            return
        copy[r][c] = 0
        cells.append(f"{r - base_r},{c - base_c}")
        dfs(r + 1, c, base_r, base_c, cells)
        dfs(r - 1, c, base_r, base_c, cells)
        dfs(r, c + 1, base_r, base_c, cells)
        dfs(r, c - 1, base_r, base_c, cells)

    for r in range(rows):
        for c in range(cols):
            if copy[r][c] == 1:
                cells = []
                dfs(r, c, r, c, cells)
                cells.sort()
                shapes.add(";".join(cells))
    return len(shapes)


class Solution:
    def numDistinctIslands(self, grid: list[list[int]]) -> int:
        return solve(grid)
