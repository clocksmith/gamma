"""2684. Maximum Number of Moves in a Grid: compute longest increasing moves one column at a time from right to left."""


def solve(grid: list[list[int]]) -> int:
    """O(r * c) time and O(r) auxiliary space; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    following = [0] * rows
    for column in range(columns - 2, -1, -1):
        current = [0] * rows
        for row in range(rows):
            for neighbor in range(max(0, row - 1), min(rows, row + 2)):
                if grid[neighbor][column + 1] > grid[row][column]:
                    current[row] = max(current[row], following[neighbor] + 1)
        following = current
    return max(following)


class Solution:
    def maxMoves(self, grid: list[list[int]]) -> int:
        return solve(grid)
