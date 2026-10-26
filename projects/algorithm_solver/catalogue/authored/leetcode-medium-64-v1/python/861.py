"""861. Score After Flipping Matrix: account for row flips and select each column majority without modifying the grid."""


def solve(grid: list[list[int]]) -> int:
    """O(rows * columns) time and O(1) auxiliary space; inputs are read-only."""
    rows = len(grid)
    answer = 0
    for column in range(len(grid[0])):
        ones = sum(row[column] == row[0] for row in grid)
        answer = answer * 2 + max(ones, rows - ones)
    return answer


class Solution:
    def matrixScore(self, grid: list[list[int]]) -> int:
        return solve(grid)
