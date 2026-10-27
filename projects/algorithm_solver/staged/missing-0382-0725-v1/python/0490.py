"""490. The Maze."""

from collections import deque

def solve(maze: list[list[int]], start: list[int], destination: list[int]) -> bool:
    rows, cols = len(maze), len(maze[0])
    source, target = tuple(start), tuple(destination)
    queue = deque([source])
    seen = {source}
    while queue:
        row, col = queue.popleft()
        if (row, col) == target:
            return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = row, col
            while 0 <= nr + dr < rows and 0 <= nc + dc < cols and maze[nr + dr][nc + dc] == 0:
                nr += dr
                nc += dc
            if (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return False


class Solution:
    def hasPath(self, maze: list[list[int]], start: list[int], destination: list[int]) -> bool:
        return solve(maze, start, destination)
