"""361. Bomb Enemy."""
def solve(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    rows, columns = len(grid), len(grid[0])
    column_hits = [0] * columns
    best = 0
    for row in range(rows):
        row_hits = 0
        for column in range(columns):
            if column == 0 or grid[row][column - 1] == 'W':
                row_hits = 0
                index = column
                while index < columns and grid[row][index] != 'W':
                    row_hits += grid[row][index] == 'E'
                    index += 1
            if row == 0 or grid[row - 1][column] == 'W':
                column_hits[column] = 0
                index = row
                while index < rows and grid[index][column] != 'W':
                    column_hits[column] += grid[index][column] == 'E'
                    index += 1
            if grid[row][column] == '0':
                best = max(best, row_hits + column_hits[column])
    return best

class Solution:
    def maxKilledEnemies(self, grid):
        return solve(grid)
