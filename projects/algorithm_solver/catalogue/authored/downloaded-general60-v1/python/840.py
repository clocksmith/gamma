"""840. Magic Squares In Grid (Medium).

Specification: https://leetcode.com/problems/magic-squares-in-grid/description/
"""


def _is_magic(grid, r, c):
    values = [grid[r + i][c + j] for i in range(3) for j in range(3)]
    if sorted(values) != list(range(1, 10)):
        return False
    for i in range(3):
        if grid[r + i][c] + grid[r + i][c + 1] + grid[r + i][c + 2] != 15:
            return False
        if grid[r][c + i] + grid[r + 1][c + i] + grid[r + 2][c + i] != 15:
            return False
    if grid[r][c] + grid[r + 1][c + 1] + grid[r + 2][c + 2] != 15:
        return False
    if grid[r][c + 2] + grid[r + 1][c + 1] + grid[r + 2][c] != 15:
        return False
    return True


def solve(grid: list[list[int]]) -> int:
    count = 0
    for r in range(len(grid) - 2):
        for c in range(len(grid[0]) - 2):
            if _is_magic(grid, r, c):
                count += 1
    return count


class Solution:
    def numMagicSquaresInside(self, grid: list[list[int]]) -> int:
        return solve(grid)
