"""Original frontend 286 variant; qualification unknown."""

from collections import deque


def solve(rooms):
    INF = 2147483647
    grid = [list(row) for row in rooms]
    m, n = len(grid), len(grid[0])
    q = deque()
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 0:
                q.append((r, c))
    while q:
        r, c = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == INF:
                grid[nr][nc] = grid[r][c] + 1
                q.append((nr, nc))
    return grid


wallsAndGates = solve


class Solution:
    def wallsAndGates(self, rooms):
        return solve(rooms)
