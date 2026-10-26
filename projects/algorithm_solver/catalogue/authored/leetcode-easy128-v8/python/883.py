"""883. Projection Area of 3D Shapes (Easy).

Specification: https://leetcode.com/problems/projection-area-of-3d-shapes/description/
"""


def solve(grid: list[list[int]]) -> int:
    """O(n^2) time, O(1) auxiliary space; count occupied cells and maxima on both axes."""
    area = 0
    for index in range(len(grid)):
        row_maximum = column_maximum = 0
        for other in range(len(grid)):
            if grid[index][other] > 0:
                area += 1
            row_maximum = max(row_maximum, grid[index][other])
            column_maximum = max(column_maximum, grid[other][index])
        area += row_maximum + column_maximum
    return area


class Solution:
    def projectionArea(self, grid: list[list[int]]) -> int:
        return solve(grid)
