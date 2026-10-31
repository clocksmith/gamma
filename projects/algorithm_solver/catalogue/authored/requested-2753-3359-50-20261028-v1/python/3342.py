"""Original frontend 3342 variant; qualification unknown."""

import heapq


def solve(moveTime) -> int:
    n, m = len(moveTime), len(moveTime[0])
    INF = 10**18
    dist = [[INF] * m for _ in range(n)]
    dist[0][0] = 0
    pq = [(0, 0, 0)]
    while pq:
        t, r, c = heapq.heappop(pq)
        if t > dist[r][c]:
            continue
        if r == n - 1 and c == m - 1:
            return t
        step = 1 + ((r + c) & 1)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < m:
                nt = max(t, moveTime[nr][nc]) + step
                if nt < dist[nr][nc]:
                    dist[nr][nc] = nt
                    heapq.heappush(pq, (nt, nr, nc))
    return dist[n - 1][m - 1]


minTimeToReach = solve


class Solution:
    def minTimeToReach(self, moveTime) -> int:
        return solve(moveTime)
