"""1267. Count Servers that Communicate: count occupied rows and columns before identifying isolated servers."""


def solve(grid: list[list[int]]) -> int:
    """O(r * c) time and O(r + c) auxiliary space; inputs are read-only."""
    rows, cols = len(grid), len(grid[0])
    row_count = [0] * rows
    col_count = [0] * cols
    for row in range(rows):
        for col in range(cols):
            if grid[row][col]:
                row_count[row] += 1
                col_count[col] += 1
    return sum(1 for row in range(rows) for col in range(cols)
               if grid[row][col] and (row_count[row] > 1 or col_count[col] > 1))


class Solution:
    def countServers(self, grid: list[list[int]]) -> int:
        return solve(grid)
