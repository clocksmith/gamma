"""3243. Shortest Distance After Road Addition Queries I (Medium).

Specification: https://leetcode.com/problems/shortest-distance-after-road-addition-queries-i/description/
"""


def solve(n: int, queries: list[list[int]]) -> list[int]:
    from collections import deque
    graph = [[] for _ in range(n)]
    for i in range(n - 1):
        graph[i].append(i + 1)

    def bfs():
        dist = [-1] * n
        dist[0] = 0
        queue = deque([0])
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if dist[v] == -1:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return dist[n - 1]

    ans = []
    for u, v in queries:
        graph[u].append(v)
        ans.append(bfs())
    return ans


class Solution:
    def shortestDistanceAfterQueries(self, n, queries):
        return solve(n, queries)
