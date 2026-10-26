"""1557. Minimum Number of Vertices to Reach All Nodes: select exactly the zero-indegree vertices of the directed acyclic graph."""


def solve(n: int, edges: list[list[int]]) -> list[int]:
    """O(n + e) time and O(n) auxiliary space; inputs are read-only."""
    incoming = [False] * n
    for start, end in edges:
        incoming[end] = True
    return [node for node in range(n) if not incoming[node]]


class Solution:
    def findSmallestSetOfVertices(self, n: int, edges: list[list[int]]) -> list[int]:
        return solve(n, edges)
