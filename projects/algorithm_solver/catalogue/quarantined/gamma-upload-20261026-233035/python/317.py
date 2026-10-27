"""317. Shortest Distance from All Buildings."""
from collections import deque

def solve(grid: list[list[int]]) -> int:
    rows, columns = len(grid), len(grid[0])
    distance = [[0] * columns for _ in range(rows)]
    reach = [[0] * columns for _ in range(rows)]
    buildings = 0
    for row in range(rows):
        for column in range(columns):
            if grid[row][column] != 1:
                continue
            buildings += 1
            queue = deque([(row, column, 0)])
            seen = {(row, column)}
            while queue:
                current_row, current_column, steps = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = current_row + dr, current_column + dc
                    if 0 <= nr < rows and 0 <= nc < columns and grid[nr][nc] == 0 and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        distance[nr][nc] += steps + 1
                        reach[nr][nc] += 1
                        queue.append((nr, nc, steps + 1))
    values = [distance[row][column] for row in range(rows) for column in range(columns)
              if grid[row][column] == 0 and reach[row][column] == buildings]
    return min(values, default=-1)

class Solution:
    def shortestDistance(self, grid):
        return solve(grid)
