"""2577. Minimum Time to Visit a Cell In a Grid. Dijkstra with two-step waiting parity after a legal first move."""

from heapq import heappop, heappush


def solve(grid: list[list[int]]) -> int:
    """O(m*n log(m*n)) time and O(m*n) space. Inputs are preserved."""
    rows, columns = len(grid), len(grid[0])
    if rows == 1 and columns == 1:
        return 0
    if not ((rows > 1 and grid[1][0] <= 1) or (columns > 1 and grid[0][1] <= 1)):
        return -1
    distance = [[float("inf")] * columns for _ in range(rows)]
    distance[0][0] = 0
    heap = [(0, 0, 0)]
    while heap:
        elapsed, row, column = heappop(heap)
        if elapsed != distance[row][column]:
            continue
        if row == rows - 1 and column == columns - 1:
            return elapsed
        for next_row, next_column in ((row - 1, column), (row + 1, column),
                                      (row, column - 1), (row, column + 1)):
            if not (0 <= next_row < rows and 0 <= next_column < columns):
                continue
            arrival = elapsed + 1
            gate = grid[next_row][next_column]
            if arrival < gate:
                arrival = gate + (gate - arrival) % 2
            if arrival < distance[next_row][next_column]:
                distance[next_row][next_column] = arrival
                heappush(heap, (arrival, next_row, next_column))
    return -1


class Solution:
    def minimumTime(self, grid: list[list[int]]) -> int:
        return solve(grid)
