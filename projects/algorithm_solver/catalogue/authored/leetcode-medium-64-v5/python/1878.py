"""1878. Get Biggest Three Rhombus Sums in a Grid: sum four diagonal borders and remove their double-counted corners."""


def solve(grid: list[list[int]]) -> list[int]:
    """O(rows * columns * min(rows, columns)) time and O(rows * columns) auxiliary space; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    down_right = [[0] * (columns + 1) for _ in range(rows + 1)]
    down_left = [[0] * (columns + 1) for _ in range(rows + 1)]
    for row in range(rows):
        for column in range(columns):
            down_right[row + 1][column + 1] = grid[row][column] + down_right[row][column]
            down_left[row + 1][column] = grid[row][column] + down_left[row][column + 1]
    largest = set()

    def retain(value: int) -> None:
        largest.add(value)
        if len(largest) > 3:
            largest.remove(min(largest))

    for row in range(rows):
        for column in range(columns):
            retain(grid[row][column])
            limit = min(row, column, rows - 1 - row, columns - 1 - column)
            for radius in range(1, limit + 1):
                total = down_right[row + 1][column + radius + 1] - down_right[row - radius][column]
                total += down_left[row + radius + 1][column] - down_left[row][column + radius + 1]
                total += down_right[row + radius + 1][column + 1] - down_right[row][column - radius]
                total += down_left[row + 1][column - radius] - down_left[row - radius][column + 1]
                total -= (grid[row - radius][column] + grid[row][column + radius] +
                          grid[row + radius][column] + grid[row][column - radius])
                retain(total)
    return sorted(largest, reverse=True)


class Solution:
    def getBiggestThree(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
