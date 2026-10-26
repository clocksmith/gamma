"""2304. Minimum Path Cost in a Grid: compute each row from the cheapest complete suffix paths in the next row."""


def solve(grid: list[list[int]], moveCost: list[list[int]]) -> int:
    """O(m * n^2) time and O(n) auxiliary space for m rows and n columns; inputs are read-only."""
    columns = len(grid[0])
    best = list(grid[-1])
    for row in range(len(grid) - 2, -1, -1):
        current = [0] * columns
        for column, value in enumerate(grid[row]):
            current[column] = value + min(moveCost[value][following] + best[following]
                                          for following in range(columns))
        best = current
    return min(best)


class Solution:
    def minPathCost(self, grid: list[list[int]], moveCost: list[list[int]]) -> int:
        return solve(grid, moveCost)
