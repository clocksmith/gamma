"""2596. Check Knight Tour Configuration: recover positions by visit number and check every consecutive knight move."""


def solve(grid: list[list[int]]) -> bool:
    """O(n * n) time and O(n * n) auxiliary space; inputs are read-only."""
    size = len(grid)
    if grid[0][0] != 0:
        return False
    positions = [None] * (size * size)
    for row in range(size):
        for column in range(size):
            positions[grid[row][column]] = (row, column)
    for step in range(1, size * size):
        row, column = positions[step]
        previous_row, previous_column = positions[step - 1]
        vertical = abs(row - previous_row)
        horizontal = abs(column - previous_column)
        if vertical * horizontal != 2:
            return False
    return True


class Solution:
    def checkValidGrid(self, grid: list[list[int]]) -> bool:
        return solve(grid)
