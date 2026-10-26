"""1719. Number Of Ways To Reconstruct A Tree.

Verify containment of ancestor-neighborhood sets; O(v^2 + e) time and space. Inputs are preserved.
"""

def solve(pairs: list[list[int]]) -> int:
    graph = {}
    for first, second in pairs:
        graph.setdefault(first, set()).add(second)
        graph.setdefault(second, set()).add(first)
    size = len(graph)
    root = next((node for node in graph if len(graph[node]) == size - 1), None)
    if root is None:
        return 0
    answer = 1
    for node, neighbors in graph.items():
        if node == root:
            continue
        candidates = [other for other in neighbors if len(graph[other]) >= len(neighbors)]
        if not candidates:
            return 0
        parent = min(candidates, key=lambda other: (len(graph[other]), other))
        if any(other != parent and other not in graph[parent] for other in neighbors):
            return 0
        if len(graph[parent]) == len(neighbors):
            answer = 2
    return answer


class Solution:
    def checkWays(self, pairs: list[list[int]]) -> int:
        return solve(pairs)
