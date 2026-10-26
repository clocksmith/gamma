"""3812. Minimum Edge Toggles on a Tree."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]], start: str, target: str) -> list[int]:
    """O(n) time and space; unique edge-parity solution in a tree, emitted in increasing index order."""
    graph = [[] for _ in range(n)]
    for index, (left, right) in enumerate(edges):
        graph[left].append((right, index))
        graph[right].append((left, index))
    parent = [-1] * n
    parent_edge = [-1] * n
    order = [0]
    for node in order:
        for child, edge in graph[node]:
            if child == parent[node]:
                continue
            parent[child] = node
            parent_edge[child] = edge
            order.append(child)
    parity = [int(left != right) for left, right in zip(start, target)]
    selected = [False] * (n - 1)
    for node in reversed(order[1:]):
        if parity[node]:
            selected[parent_edge[node]] = True
            parity[parent[node]] ^= 1
    if parity[0]:
        return [-1]
    return [edge for edge, needed in enumerate(selected) if needed]


class Solution:
    def minimumFlips(self, n: int, edges: list[list[int]], start: str, target: str) -> list[int]:
        return solve(n, edges, start, target)
