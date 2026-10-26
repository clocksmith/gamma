"""2493. Divide Nodes Into the Maximum Number of Groups. Reject odd cycles and maximize breadth-first layers in each component."""


def solve(n: int, edges: list[list[int]]) -> int:
    """O(n*(n+m)) time and O(n+m) space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first - 1].append(second - 1)
        graph[second - 1].append(first - 1)
    color = [-1] * n
    answer = 0
    for start in range(n):
        if color[start] != -1:
            continue
        component = [start]
        color[start] = 0
        for node in component:
            for neighbor in graph[node]:
                if color[neighbor] == -1:
                    color[neighbor] = color[node] ^ 1
                    component.append(neighbor)
                elif color[neighbor] == color[node]:
                    return -1
        largest = 1
        for root in component:
            distance = [-1] * n
            distance[root] = 0
            queue = [root]
            for node in queue:
                for neighbor in graph[node]:
                    if distance[neighbor] == -1:
                        distance[neighbor] = distance[node] + 1
                        queue.append(neighbor)
            largest = max(largest, distance[queue[-1]] + 1)
        answer += largest
    return answer


class Solution:
    def magnificentSets(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
