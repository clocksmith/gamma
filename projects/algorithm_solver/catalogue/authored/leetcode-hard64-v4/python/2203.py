"""2203. Minimum Weighted Subgraph With the Required Paths."""

from heapq import heappop, heappush


def solve(n: int, edges: list[list[int]], src1: int, src2: int, dest: int) -> int:
    """Three Dijkstra runs and a shared meeting vertex; O((V+E) log V) time and O(V+E) space. Inputs are preserved."""
    forward = [[] for _ in range(n)]
    backward = [[] for _ in range(n)]
    for source, target, weight in edges:
        forward[source].append((target, weight))
        backward[target].append((source, weight))

    def distances(start, neighbors):
        best = [float('inf')] * n
        best[start] = 0
        heap = [(0, start)]
        while heap:
            cost, node = heappop(heap)
            if cost != best[node]:
                continue
            for target, weight in neighbors[node]:
                candidate = cost + weight
                if candidate < best[target]:
                    best[target] = candidate
                    heappush(heap, (candidate, target))
        return best

    first = distances(src1, forward)
    second = distances(src2, forward)
    finish = distances(dest, backward)
    answer = min(first[node] + second[node] + finish[node] for node in range(n))
    return -1 if answer == float('inf') else answer


class Solution:
    def minimumWeight(self, n: int, edges: list[list[int]], src1: int, src2: int, dest: int) -> int:
        return solve(n, edges, src1, src2, dest)
