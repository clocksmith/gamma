"""2699. Modify Graph Edge Weights. Two Dijkstra passes distribute the target slack over adjustable edges."""

from heapq import heappop, heappush


def solve(n: int, edges: list[list[int]], source: int, destination: int, target: int) -> list[list[int]]:
    """O((n+m) log(n+m)) time and O(n+m) space. Inputs are preserved."""
    result = [edge.copy() for edge in edges]
    graph = [[] for _ in range(n)]
    for index, (first, second, _) in enumerate(result):
        graph[first].append((second, index))
        graph[second].append((first, index))

    def shortest(baseline=None, slack=0):
        distance = [float("inf")] * n
        distance[source] = 0
        heap = [(0, source)]
        while heap:
            elapsed, node = heappop(heap)
            if elapsed != distance[node]:
                continue
            for neighbor, index in graph[node]:
                weight = result[index][2]
                if weight == -1:
                    weight = 1
                    if baseline is not None:
                        proposed = slack + baseline[neighbor] - elapsed
                        if proposed > 1:
                            weight = proposed
                            result[index][2] = weight
                arrival = elapsed + weight
                if arrival < distance[neighbor]:
                    distance[neighbor] = arrival
                    heappush(heap, (arrival, neighbor))
        return distance

    baseline = shortest()
    slack = target - baseline[destination]
    if slack < 0:
        return []
    distance = shortest(baseline, slack)
    if distance[destination] != target:
        return []
    for edge in result:
        if edge[2] == -1:
            edge[2] = 1
    return result


class Solution:
    def modifiedGraphEdges(self, n: int, edges: list[list[int]], source: int, destination: int, target: int) -> list[list[int]]:
        return solve(n, edges, source, destination, target)
