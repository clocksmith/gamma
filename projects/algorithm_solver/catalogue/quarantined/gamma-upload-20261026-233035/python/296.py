"""296. Best Meeting Point."""
def solve(grid: list[list[int]]) -> int:
    rows = [row for row in range(len(grid)) for column in range(len(grid[0])) if grid[row][column] == 1]
    columns = [column for column in range(len(grid[0])) for row in range(len(grid)) if grid[row][column] == 1]
    row_median = rows[len(rows) // 2]
    column_median = columns[len(columns) // 2]
    return sum(abs(row - row_median) for row in rows) + sum(abs(column - column_median) for column in columns)

class Solution:
    def minTotalDistance(self, grid: list[list[int]]) -> int:
        return solve(grid)
