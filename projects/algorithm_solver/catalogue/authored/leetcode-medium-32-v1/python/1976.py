"""1976. Number of Ways to Arrive at Destination: count shortest paths during Dijkstra relaxation."""


def solve(n: int, roads: list[list[int]]) -> int:
    """O(n^2 + e) time and O(n + e) auxiliary space; inputs are read-only."""
    modulus = 1_000_000_007
    graph = [[] for _ in range(n)]
    for start, end, duration in roads:
        graph[start].append((end, duration))
        graph[end].append((start, duration))
    distances = [float("inf")] * n
    ways = [0] * n
    settled = [False] * n
    distances[0] = 0
    ways[0] = 1

    # The declared n <= 200 bound permits an allocation-light dense selection.
    for _ in range(n):
        node = -1
        for candidate in range(n):
            if not settled[candidate] and (node == -1 or distances[candidate] < distances[node]):
                node = candidate
        if node == -1 or distances[node] == float("inf"):
            break
        if node == n - 1:
            break
        settled[node] = True
        for neighbor, duration in graph[node]:
            distance = distances[node] + duration
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                ways[neighbor] = ways[node]
            elif distance == distances[neighbor]:
                ways[neighbor] = (ways[neighbor] + ways[node]) % modulus
    return ways[n - 1]


class Solution:
    def countPaths(self, n: int, roads: list[list[int]]) -> int:
        return solve(n, roads)
