"""685. Redundant Connection II. Separate the two-parent case from the cycle case; preserve every input edge."""

class _DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        return True

def solve(edges: list[list[int]]) -> list[int]:
    n = len(edges)
    parent_edge = [-1] * (n + 1)
    first = second = -1
    for index, (_, target) in enumerate(edges):
        if parent_edge[target] != -1:
            first, second = parent_edge[target], index
        else:
            parent_edge[target] = index
    dsu = _DSU(n + 1)
    for index, (source, target) in enumerate(edges):
        if index == second:
            continue
        if not dsu.union(source, target):
            return edges[first][:] if first != -1 else [source, target]
    return edges[second][:] if second != -1 else []


class Solution:
    def findRedundantDirectedConnection(self, edges: list[list[int]]) -> list[int]:
        return solve(edges)
