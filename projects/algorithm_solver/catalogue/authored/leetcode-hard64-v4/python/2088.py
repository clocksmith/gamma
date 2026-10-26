"""2088. Count Fertile Pyramids in a Land."""


def solve(grid: list[list[int]]) -> int:
    """Two directional height DPs; O(R*C) time and O(C) auxiliary space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    answer = 0
    for order in (range(rows), range(rows - 1, -1, -1)):
        previous = [0] * columns
        for row in order:
            current = [0] * columns
            for column in range(columns):
                if grid[row][column] == 0:
                    continue
                current[column] = 1
                if 0 < column < columns - 1:
                    current[column] += min(previous[column - 1], previous[column], previous[column + 1])
                answer += current[column] - 1
            previous = current
    return answer


class Solution:
    def countPyramids(self, grid: list[list[int]]) -> int:
        return solve(grid)
