"""3459. Length of Longest V-Shaped Diagonal Segment: join a one-starting prefix with a clockwise alternating diagonal suffix."""

from array import array


def solve(grid: list[list[int]]) -> int:
    """O(rows*columns) time and O(rows*columns) auxiliary space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    directions = ((1, 1), (1, -1), (-1, -1), (-1, 1))
    tails = []
    for dx, dy in directions:
        tail = array('H', [0]) * (rows * columns)
        row_order = range(rows - 1, -1, -1) if dx > 0 else range(rows)
        for row in row_order:
            for column in range(columns):
                index = row * columns + column
                tail[index] = 1
                following_row, following_column = row + dx, column + dy
                expected = 2 if grid[row][column] == 1 else 2 - grid[row][column]
                if 0 <= following_row < rows and 0 <= following_column < columns and grid[following_row][following_column] == expected:
                    tail[index] += tail[following_row * columns + following_column]
        tails.append(tail)
    answer = 0
    for direction, (dx, dy) in enumerate(directions):
        prefix = array('H', [0]) * (rows * columns)
        row_order = range(rows) if dx > 0 else range(rows - 1, -1, -1)
        for row in row_order:
            for column in range(columns):
                index = row * columns + column
                if grid[row][column] == 1:
                    prefix[index] = 1
                else:
                    previous_row, previous_column = row - dx, column - dy
                    if 0 <= previous_row < rows and 0 <= previous_column < columns:
                        previous_index = previous_row * columns + previous_column
                        previous_value = grid[previous_row][previous_column]
                        expected = 2 if previous_value == 1 else 2 - previous_value
                        if prefix[previous_index] and grid[row][column] == expected:
                            prefix[index] = prefix[previous_index] + 1
                if prefix[index]:
                    answer = max(answer, prefix[index] + tails[(direction + 1) % 4][index] - 1)
    return answer


class Solution:
    def lenOfVDiagonal(self, grid: list[list[int]]) -> int:
        return solve(grid)
