"""1368. Minimum Cost to Make at Least One Valid Path in a Grid: 0-1 BFS, with zero cost for following an arrow; O(rows*columns) time and space."""

from collections import deque


def solve(grid: list[list[int]]) -> int:
    rows, columns = len(grid), len(grid[0])
    distance = [[float('inf')] * columns for _ in range(rows)]
    distance[0][0] = 0
    queue = deque([(0, 0, 0)])
    directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
    while queue:
        row, column, cost = queue.popleft()
        if cost != distance[row][column]:
            continue
        if row == rows - 1 and column == columns - 1:
            return cost
        for arrow, (dr, dc) in enumerate(directions, 1):
            nr, nc = row + dr, column + dc
            if not (0 <= nr < rows and 0 <= nc < columns):
                continue
            extra = int(grid[row][column] != arrow)
            following = cost + extra
            if following < distance[nr][nc]:
                distance[nr][nc] = following
                if extra:
                    queue.append((nr, nc, following))
                else:
                    queue.appendleft((nr, nc, following))
    return -1


class Solution:
    def minCost(self, grid: list[list[int]]) -> int:
        return solve(grid)
