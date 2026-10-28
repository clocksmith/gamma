"""1034. Coloring A Border (Medium).

Specification: https://leetcode.com/problems/coloring-a-border/description/
"""


def solve(grid: list[list[int]], row: int, col: int, color: int) -> list[list[int]]:
    rows, cols = len(grid), len(grid[0])
    original = grid[row][col]
    result = [line[:] for line in grid]
    visited = {(row, col)}
    stack = [(row, col)]
    while stack:
        r, c = stack.pop()
        border = False
        for a, b in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if not (0 <= a < rows and 0 <= b < cols) or grid[a][b] != original:
                border = True
            elif (a, b) not in visited:
                visited.add((a, b))
                stack.append((a, b))
        if border:
            result[r][c] = color
    return result

class Solution:
    def colorBorder(self, grid: list[list[int]], row: int, col: int, color: int) -> list[list[int]]:
        return solve(grid, row, col, color)
