"""1463. Cherry Pickup II: two-robot row DP; O(rows*columns^2) time and O(columns^2) space. Inputs are preserved."""


def solve(grid: list[list[int]]) -> int:
    columns = len(grid[0])
    following = [[0] * columns for _ in range(columns)]
    for row in reversed(grid):
        current = [[0] * columns for _ in range(columns)]
        for first in range(columns):
            for second in range(columns):
                best = 0
                for next_first in range(max(0, first - 1), min(columns, first + 2)):
                    for next_second in range(max(0, second - 1), min(columns, second + 2)):
                        best = max(best, following[next_first][next_second])
                current[first][second] = row[first] + (row[second] if first != second else 0) + best
        following = current
    return following[0][-1]


class Solution:
    def cherryPickup(self, grid: list[list[int]]) -> int:
        return solve(grid)
