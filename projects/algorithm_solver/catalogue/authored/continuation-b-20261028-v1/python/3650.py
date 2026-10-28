from heapq import heappop, heappush

def solve(n, edges):
    graph = [[] for _ in range(n)]
    for u, v, w in edges:
        graph[u].append((v, w))
        graph[v].append((u, 2*w))
    dist = [float('inf')]*n
    dist[0] = 0
    heap = [(0, 0)]
    while heap:
        cost, u = heappop(heap)
        if cost != dist[u]: continue
        if u == n-1: return cost
        for v, weight in graph[u]:
            candidate = cost+weight
            if candidate < dist[v]:
                dist[v] = candidate
                heappush(heap, (candidate, v))
    return -1

class Solution:
    def minCost(self, n, edges):
        return solve(n, edges)
