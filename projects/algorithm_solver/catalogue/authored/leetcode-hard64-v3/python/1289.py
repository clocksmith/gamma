"""1289. Minimum Falling Path Sum II: two row minima; O(n^2) time and O(n) space. Inputs are preserved."""


def solve(grid: list[list[int]]) -> int:
    best = grid[0][:]
    for row in grid[1:]:
        first = second = float('inf')
        first_column = -1
        for column, value in enumerate(best):
            if value < first:
                second, first = first, value
                first_column = column
            elif value < second:
                second = value
        best = [value + (second if column == first_column else first)
                for column, value in enumerate(row)]
    return min(best)


class Solution:
    def minFallingPathSum(self, grid: list[list[int]]) -> int:
        return solve(grid)
