"""934. Shortest Bridge: flood one island then expand a multi-source breadth-first search."""


def solve(grid: list[list[int]]) -> int:
    """O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only."""
    rows, columns = len(grid), len(grid[0])
    seen = [[False] * columns for _ in grid]
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    start = next((row, column) for row in range(rows) for column in range(columns)
                 if grid[row][column] == 1)
    stack = [start]
    seen[start[0]][start[1]] = True
    queue = []
    while stack:
        row, column = stack.pop()
        queue.append((row, column))
        for dr, dc in directions:
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and not seen[nr][nc] and grid[nr][nc] == 1:
                seen[nr][nc] = True
                stack.append((nr, nc))
    head = 0
    distance = 0
    while head < len(queue):
        layer_end = len(queue)
        while head < layer_end:
            row, column = queue[head]
            head += 1
            for dr, dc in directions:
                nr, nc = row + dr, column + dc
                if 0 <= nr < rows and 0 <= nc < columns and not seen[nr][nc]:
                    if grid[nr][nc] == 1:
                        return distance
                    seen[nr][nc] = True
                    queue.append((nr, nc))
        distance += 1
    return -1


class Solution:
    def shortestBridge(self, grid: list[list[int]]) -> int:
        return solve(grid)
