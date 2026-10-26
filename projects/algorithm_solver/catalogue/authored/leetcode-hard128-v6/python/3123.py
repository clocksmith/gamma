"""3123. Find Edges in Shortest Paths.

Dijkstra from both endpoints identifies every edge on a shortest path; O((n+e) log n) time, O(n+e) space. Inputs are preserved.
"""

from heapq import heappop, heappush


def solve(n: int, edges: list[list[int]]) -> list[bool]:
    graph = [[] for _ in range(n)]
    for a, b, weight in edges:
        graph[a].append((b, weight))
        graph[b].append((a, weight))

    def distances(start):
        result = [float('inf')] * n
        result[start] = 0
        queue = [(0, start)]
        while queue:
            distance, node = heappop(queue)
            if distance != result[node]:
                continue
            for neighbor, weight in graph[node]:
                candidate = distance + weight
                if candidate < result[neighbor]:
                    result[neighbor] = candidate
                    heappush(queue, (candidate, neighbor))
        return result

    first, last = distances(0), distances(n - 1)
    shortest = first[-1]
    if shortest == float('inf'):
        return [False] * len(edges)
    return [first[a] + weight + last[b] == shortest or first[b] + weight + last[a] == shortest for a, b, weight in edges]


class Solution:
    def findAnswer(self, n: int, edges: list[list[int]]) -> list[bool]:
        return solve(n, edges)
