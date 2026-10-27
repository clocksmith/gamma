"""3970. Shortest Path With At Most K Consecutive Identical Characters.

Specification: https://leetcode.com/problems/shortest-path-with-at-most-k-consecutive-identical-characters/description/
"""

from __future__ import annotations
from heapq import heappop, heappush


def solve(n: int, edges: list[list[int]], labels: str, k: int) -> int:
    """O(k (n+m) log(nk)) time and O(nk+mk) worst-case space; Dijkstra on node/run-length states. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for source, target, weight in edges:
        graph[source].append((target, weight))
    width = k + 1
    distance = [float('inf')] * (n * width)
    settled_run = [width] * n
    distance[1] = 0
    heap = [(0, 0, 1)]
    while heap:
        cost, node, run = heappop(heap)
        if distance[node * width + run] != cost or settled_run[node] <= run:
            continue
        settled_run[node] = run
        if node == n - 1:
            return cost
        for next_node, weight in graph[node]:
            next_run = run + 1 if labels[next_node] == labels[node] else 1
            if next_run > k or settled_run[next_node] <= next_run:
                continue
            state = next_node * width + next_run
            next_cost = cost + weight
            if next_cost < distance[state]:
                distance[state] = next_cost
                heappush(heap, (next_cost, next_node, next_run))
    return -1

# Native judge method name is not established; canonical solve is the supported entry point.
