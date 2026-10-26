"""3882. Minimum XOR Path in a Grid."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> int:
    """O(rows*columns*2^10) time and O(columns*2^10) space; retain all reachable XOR states, not just local minima."""
    rows, columns = len(grid), len(grid[0])
    paths = [set() for _ in range(columns)]
    for row in range(rows):
        for column in range(columns):
            value = grid[row][column]
            if row == 0 and column == 0:
                paths[column] = {value}
                continue
            reachable = {state ^ value for state in paths[column]}
            if column:
                reachable.update(state ^ value for state in paths[column - 1])
            paths[column] = reachable
    return min(paths[-1])


class Solution:
    def minXor(self, grid: list[list[int]]) -> int:
        return solve(grid)
