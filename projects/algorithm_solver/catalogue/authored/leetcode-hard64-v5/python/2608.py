"""2608. Shortest Cycle in a Graph. Breadth-first search from each vertex with non-parent edge detection."""


def solve(n: int, edges: list[list[int]]) -> int:
    """O(n*(n+m)) time and O(n+m) space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    answer = n + 1
    for start in range(n):
        distance = [-1] * n
        parent = [-1] * n
        distance[start] = 0
        queue = [start]
        for node in queue:
            for neighbor in graph[node]:
                if distance[neighbor] == -1:
                    distance[neighbor] = distance[node] + 1
                    parent[neighbor] = node
                    queue.append(neighbor)
                elif parent[node] != neighbor:
                    answer = min(answer, distance[node] + distance[neighbor] + 1)
        if answer == 3:
            return 3
    return answer if answer <= n else -1


class Solution:
    def findShortestCycle(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
