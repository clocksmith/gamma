"""Original frontend 3313 variant; qualification unknown."""

from collections import deque


def solve(edges):
    n = len(edges) + 1
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    def bfs(start: int):
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        last = start
        while q:
            u = q.popleft()
            last = u
            for v in adj[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return last, dist

    a, _ = bfs(0)
    b, da = bfs(a)
    _, db = bfs(b)
    return [a if da[i] >= db[i] else b for i in range(n)]


lastMarkedNodes = solve


class Solution:
    def lastMarkedNodes(self, edges):
        return solve(edges)
