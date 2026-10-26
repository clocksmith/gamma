"""2685. Count the Number of Complete Components: compare the total degree of each connected component with its complete-graph size."""


def solve(n: int, edges: list[list[int]]) -> int:
    """O(n + e) time and O(n + e) auxiliary space; inputs are read-only."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    seen = [False] * n
    complete = 0
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        size = degree = 0
        while stack:
            node = stack.pop()
            size += 1
            degree += len(graph[node])
            for neighbor in graph[node]:
                if not seen[neighbor]:
                    seen[neighbor] = True
                    stack.append(neighbor)
        if degree == size * (size - 1):
            complete += 1
    return complete


class Solution:
    def countCompleteComponents(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
