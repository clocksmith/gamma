"""3650. Minimum Cost Path with Edge Reversals.

Specification: https://leetcode.com/problems/minimum-cost-path-with-edge-reversals/description/
Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
O((n + e) log(n + e)) time, O(n + e) space; a positive-weight optimal path never revisits a vertex.
Inputs are not modified.
"""

from heapq import heappush, heappop

def solve(n, edges):
    graph = [[] for _ in range(n)]
    for source, target, weight in edges:
        graph[source].append((target, weight))
        graph[target].append((source, 2 * weight))
    distance = [float('inf')] * n
    distance[0] = 0
    heap = [(0, 0)]
    while heap:
        cost, node = heappop(heap)
        if cost != distance[node]:
            continue
        if node == n - 1:
            return cost
        for target, weight in graph[node]:
            following = cost + weight
            if following < distance[target]:
                distance[target] = following
                heappush(heap, (following, target))
    return -1


class Solution:
    def minCost(self, n, edges):
        return solve(n, edges)
