"""1706. Where Will the Ball Fall: follow each ball through adjacent boards of matching slope."""


def solve(grid: list[list[int]]) -> list[int]:
    """O(rows * columns) time and O(columns) output space; inputs are read-only."""
    columns = len(grid[0])
    result = []
    for start in range(columns):
        column = start
        for row in grid:
            neighbor = column + row[column]
            if neighbor < 0 or neighbor >= columns or row[neighbor] != row[column]:
                column = -1
                break
            column = neighbor
        result.append(column)
    return result


class Solution:
    def findBall(self, grid: list[list[int]]) -> list[int]:
        return solve(grid)
