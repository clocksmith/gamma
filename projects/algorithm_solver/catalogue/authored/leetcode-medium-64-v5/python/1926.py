"""1926. Nearest Exit from Entrance in Maze: search outward by distance without changing walls or counting the entrance as an exit."""
from collections import deque


def solve(maze: list[list[str]], entrance: list[int]) -> int:
    """O(rows * columns) time and O(rows * columns) auxiliary space; inputs are read-only."""
    rows, columns = len(maze), len(maze[0])
    start_row, start_column = entrance
    seen = [bytearray(columns) for _ in range(rows)]
    seen[start_row][start_column] = 1
    queue = deque([(start_row, start_column, 0)])
    while queue:
        row, column, distance = queue.popleft()
        if distance > 0 and (row == 0 or row == rows - 1 or column == 0 or column == columns - 1):
            return distance
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row + dr, column + dc
            if 0 <= nr < rows and 0 <= nc < columns and maze[nr][nc] == '.' and not seen[nr][nc]:
                seen[nr][nc] = 1
                queue.append((nr, nc, distance + 1))
    return -1


class Solution:
    def nearestExit(self, maze: list[list[str]], entrance: list[int]) -> int:
        return solve(maze, entrance)
