"""3742. Maximum Path Score in a Grid."""
from __future__ import annotations


def solve(grid: list[list[int]], k: int) -> int:
    """O(rows * columns * min(k + 1, rows + columns)) time and O(columns * min(k + 1, rows + columns)) space."""
    rows, columns = len(grid), len(grid[0])
    limit = min(k, rows + columns - 1)
    previous = [[-1] * (limit + 1) for _ in range(columns)]
    for row in range(rows):
        for column in range(columns):
            value = grid[row][column]
            cost = int(value != 0)
            current = [-1] * (limit + 1)
            if row == 0 and column == 0:
                current[0] = 0
            else:
                for spent in range(cost, limit + 1):
                    best = previous[column][spent - cost] if row else -1
                    if column:
                        best = max(best, previous[column - 1][spent - cost])
                    if best >= 0:
                        current[spent] = best + value
            previous[column] = current
    return max(previous[-1])


class Solution:
    def maxPathScore(self, grid: list[list[int]], k: int) -> int:
        return solve(grid, k)
