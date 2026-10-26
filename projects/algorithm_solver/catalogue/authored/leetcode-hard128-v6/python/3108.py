"""3108. Minimum Cost Walk in Weighted Graph.

A walk may include every edge in its connected component; union-find plus component AND. O((n+e+q)*alpha(n)) time, O(n) space. Inputs are preserved.
"""

def solve(n: int, edges: list[list[int]], query: list[list[int]]) -> list[int]:
    parent = list(range(n))
    size = [1] * n

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for a, b, _ in edges:
        a, b = find(a), find(b)
        if a != b:
            if size[a] < size[b]:
                a, b = b, a
            parent[b] = a
            size[a] += size[b]
    value = [-1] * n
    for a, _, weight in edges:
        value[find(a)] &= weight
    return [0 if a == b else value[find(a)] if find(a) == find(b) else -1 for a, b in query]


class Solution:
    def minimumCost(self, n: int, edges: list[list[int]], query: list[list[int]]) -> list[int]:
        return solve(n, edges, query)
