"""1992. Find All Groups of Farmland: identify each rectangular group by its top-left corner and trace its two dimensions."""


def solve(land: list[list[int]]) -> list[list[int]]:
    """O(rows * columns) time and O(groups) output space with O(1) auxiliary space; inputs are read-only."""
    rows, columns = len(land), len(land[0])
    result = []
    for row in range(rows):
        for column in range(columns):
            if land[row][column] == 0:
                continue
            if row > 0 and land[row - 1][column] == 1:
                continue
            if column > 0 and land[row][column - 1] == 1:
                continue
            bottom, right = row, column
            while bottom + 1 < rows and land[bottom + 1][column] == 1:
                bottom += 1
            while right + 1 < columns and land[row][right + 1] == 1:
                right += 1
            result.append([row, column, bottom, right])
    return result


class Solution:
    def findFarmland(self, land: list[list[int]]) -> list[list[int]]:
        return solve(land)
