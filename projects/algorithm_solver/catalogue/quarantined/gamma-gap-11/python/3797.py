"""3797. Count Routes to Climb a Rectangular Grid."""
from __future__ import annotations


def solve(grid: list[str], d: int) -> int:
    """O(rows * columns) time and O(columns) space; vertical radius is d-1 and each row permits zero or one horizontal move."""
    modulus = 1_000_000_007
    columns = len(grid[0])
    def window_sums(values, radius):
        prefix = [0]
        for value in values:
            prefix.append((prefix[-1] + value) % modulus)
        return [(prefix[min(columns, index + radius + 1)] - prefix[max(0, index - radius)]) % modulus for index in range(columns)]
    previous = None
    for row in range(len(grid) - 1, -1, -1):
        entering = [1] * columns if previous is None else window_sums(previous, d - 1)
        for column in range(columns):
            if grid[row][column] == '#':
                entering[column] = 0
        previous = window_sums(entering, d)
        for column in range(columns):
            if grid[row][column] == '#':
                previous[column] = 0
    return sum(previous) % modulus


class Solution:
    def numberOfRoutes(self, grid: list[str], d: int) -> int:
        return solve(grid, d)
