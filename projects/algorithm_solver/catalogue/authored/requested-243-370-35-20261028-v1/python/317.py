"""Original frontend 317 variant; qualification unknown."""

from collections import deque


def solve(grid) -> int:
    m, n = len(grid), len(grid[0])
    total_dist = [[0] * n for _ in range(m)]
    reach = [[0] * n for _ in range(m)]
    buildings = 0
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 1:
                buildings += 1
                q = deque([(r, c, 0)])
                vis = [[False] * n for _ in range(m)]
                vis[r][c] = True
                while q:
                    cr, cc, d = q.popleft()
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < m and 0 <= nc < n and not vis[nr][nc] and grid[nr][nc] == 0:
                            vis[nr][nc] = True
                            total_dist[nr][nc] += d + 1
                            reach[nr][nc] += 1
                            q.append((nr, nc, d + 1))
    INF = 10**18
    ans = INF
    for r in range(m):
        for c in range(n):
            if grid[r][c] == 0 and reach[r][c] == buildings and total_dist[r][c] < ans:
                ans = total_dist[r][c]
    return -1 if ans == INF else ans


shortestDistance = solve


class Solution:
    def shortestDistance(self, grid) -> int:
        return solve(grid)
