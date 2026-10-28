"""1895. Largest Magic Square (Medium).

Specification: https://leetcode.com/problems/largest-magic-square/description/
"""


def _is_magic(grid, top, left, size):
    target = sum(grid[top][left + c] for c in range(size))
    for r in range(size):
        if sum(grid[top + r][left + c] for c in range(size)) != target:
            return False
    for c in range(size):
        if sum(grid[top + r][left + c] for r in range(size)) != target:
            return False
    diag1 = sum(grid[top + i][left + i] for i in range(size))
    diag2 = sum(grid[top + i][left + size - 1 - i] for i in range(size))
    return diag1 == target and diag2 == target


def solve(grid: list[list[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    for size in range(min(rows, cols), 0, -1):
        for top in range(rows - size + 1):
            for left in range(cols - size + 1):
                if _is_magic(grid, top, left, size):
                    return size
    return 1


class Solution:
    def largestMagicSquare(self, grid: list[list[int]]) -> int:
        return solve(grid)
