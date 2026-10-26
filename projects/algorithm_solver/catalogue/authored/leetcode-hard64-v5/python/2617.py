"""2617. Minimum Number of Visited Cells in a Grid. Row-major DP with expiring reachable-cell heaps per row and column."""

from heapq import heappop, heappush


def solve(grid: list[list[int]]) -> int:
    """O(m*n log(m+n)) time and O(m*n) space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    column_heaps = [[] for _ in range(columns)]
    distance = float("inf")
    for row in range(rows):
        row_heap = []
        for column in range(columns):
            column_heap = column_heaps[column]
            while row_heap and row_heap[0][1] < column:
                heappop(row_heap)
            while column_heap and column_heap[0][1] < row:
                heappop(column_heap)
            distance = 1 if row == 0 and column == 0 else float("inf")
            if row_heap:
                distance = min(distance, row_heap[0][0] + 1)
            if column_heap:
                distance = min(distance, column_heap[0][0] + 1)
            reach = grid[row][column]
            if distance != float("inf") and reach > 0:
                heappush(row_heap, (distance, column + reach))
                heappush(column_heap, (distance, row + reach))
    return distance if distance != float("inf") else -1


class Solution:
    def minimumVisitedCells(self, grid: list[list[int]]) -> int:
        return solve(grid)
