"""3071. Minimum Operations to Write the Letter Y on a Grid: count colors inside and outside the Y and choose two distinct target colors."""


def solve(grid: list[list[int]]) -> int:
    """O(n * n) time and O(1) auxiliary space; inputs are read-only."""
    size = len(grid)
    middle = size // 2
    inside = [0, 0, 0]
    outside = [0, 0, 0]
    for row in range(size):
        for column in range(size):
            belongs = ((row < middle and (column == row or column == size - 1 - row))
                       or (row >= middle and column == middle))
            counts = inside if belongs else outside
            counts[grid[row][column]] += 1
    retained = max(inside[first] + outside[second]
                   for first in range(3) for second in range(3) if first != second)
    return size * size - retained


class Solution:
    def minimumOperationsToWriteY(self, grid: list[list[int]]) -> int:
        return solve(grid)
