"""892. Surface Area of 3D Shapes (Easy).

Specification: https://leetcode.com/problems/surface-area-of-3d-shapes/description/
"""


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    area = 0
    for r in range(rows):
        for c in range(cols):
            v = grid[r][c]
            if v > 0:
                area += 4 * v + 2
            if r + 1 < rows:
                area -= 2 * min(v, grid[r + 1][c])
            if c + 1 < cols:
                area -= 2 * min(v, grid[r][c + 1])
    return area


class Solution:
    def surfaceArea(self, grid: list[list[int]]) -> int:
        return solve(grid)
