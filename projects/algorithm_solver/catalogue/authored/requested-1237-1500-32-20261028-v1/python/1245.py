"""Original frontend 1245 variant; qualification unknown."""
from collections import deque


def solve(edges) -> int:
    if not edges:
        return 0
    n = len(edges) + 1
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def farthest(start: int):
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        far = start
        while q:
            u = q.popleft()
            if dist[u] > dist[far]:
                far = u
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return far, dist[far]

    u, _ = farthest(0)
    _, d = farthest(u)
    return d


treeDiameter = solve


class Solution:
    def treeDiameter(self, edges) -> int:
        return solve(edges)
