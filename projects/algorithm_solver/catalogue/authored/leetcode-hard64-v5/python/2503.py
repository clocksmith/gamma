"""2503. Maximum Number of Points From Grid Queries. Process sorted query thresholds through a shared minimum-heap frontier."""

from heapq import heappop, heappush


def solve(grid: list[list[int]], queries: list[int]) -> list[int]:
    """O(m*n log(m*n)+q log q) time and O(m*n+q) space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    seen = [[False] * columns for _ in range(rows)]
    seen[0][0] = True
    heap = [(grid[0][0], 0, 0)]
    answer = [0] * len(queries)
    count = 0
    for threshold, index in sorted((value, index) for index, value in enumerate(queries)):
        while heap and heap[0][0] < threshold:
            _, row, column = heappop(heap)
            count += 1
            for next_row, next_column in ((row - 1, column), (row + 1, column),
                                          (row, column - 1), (row, column + 1)):
                if 0 <= next_row < rows and 0 <= next_column < columns and not seen[next_row][next_column]:
                    seen[next_row][next_column] = True
                    heappush(heap, (grid[next_row][next_column], next_row, next_column))
        answer[index] = count
    return answer


class Solution:
    def maxPoints(self, grid: list[list[int]], queries: list[int]) -> list[int]:
        return solve(grid, queries)
