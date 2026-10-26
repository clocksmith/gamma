"""2387. Median of a Row Wise Sorted Matrix: binary search values using upper bounds in each sorted row."""
from bisect import bisect_right


def solve(grid: list[list[int]]) -> int:
    """O(r log(c + 1) log(V + 1)) time and O(1) auxiliary space for value range V; inputs are read-only."""
    low = min(row[0] for row in grid)
    high = max(row[-1] for row in grid)
    middle_rank = len(grid) * len(grid[0]) // 2
    while low < high:
        middle = (low + high) // 2
        count = sum(bisect_right(row, middle) for row in grid)
        if count <= middle_rank:
            low = middle + 1
        else:
            high = middle
    return low


class Solution:
    def matrixMedian(self, grid: list[list[int]]) -> int:
        return solve(grid)
