"""1914. Cyclically Rotating a Grid: rotate each clockwise boundary sequence by a counterclockwise offset into a fresh grid."""


def solve(grid: list[list[int]], k: int) -> list[list[int]]:
    """O(rows * columns) time and output space, with O(rows + columns) auxiliary space; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    for layer in range(min(rows, columns) // 2):
        top = left = layer
        bottom, right = rows - 1 - layer, columns - 1 - layer
        boundary = []
        for column in range(left, right + 1):
            boundary.append((top, column))
        for row in range(top + 1, bottom + 1):
            boundary.append((row, right))
        for column in range(right - 1, left - 1, -1):
            boundary.append((bottom, column))
        for row in range(bottom - 1, top, -1):
            boundary.append((row, left))
        shift = k % len(boundary)
        for index, (row, column) in enumerate(boundary):
            source_row, source_column = boundary[(index + shift) % len(boundary)]
            result[row][column] = grid[source_row][source_column]
    return result


class Solution:
    def rotateGrid(self, grid: list[list[int]], k: int) -> list[list[int]]:
        return solve(grid, k)
