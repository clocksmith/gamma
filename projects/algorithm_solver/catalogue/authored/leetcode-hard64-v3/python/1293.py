"""1293. Shortest Path in a Grid with Obstacles Elimination: BFS with remaining-budget dominance; O(rows*columns*(k+1)) worst-case time and space."""

from collections import deque


def solve(grid: list[list[int]], k: int) -> int:
    rows, columns = len(grid), len(grid[0])
    if k >= rows + columns - 2:
        return rows + columns - 2
    budget = [[-1] * columns for _ in range(rows)]
    budget[0][0] = k
    queue = deque([(0, 0, k, 0)])
    while queue:
        row, column, remaining, distance = queue.popleft()
        if row == rows - 1 and column == columns - 1:
            return distance
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if not (0 <= nr < rows and 0 <= nc < columns):
                continue
            following = remaining - grid[nr][nc]
            if following >= 0 and following > budget[nr][nc]:
                budget[nr][nc] = following
                queue.append((nr, nc, following, distance + 1))
    return -1


class Solution:
    def shortestPath(self, grid: list[list[int]], k: int) -> int:
        return solve(grid, k)
