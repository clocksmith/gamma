"""684. Redundant Connection."""

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
    dsu = _DSU(len(edges) + 1)
    for a, b in edges:
        if not dsu.union(a, b):
            return [a, b]
    return []


class Solution:
    def findRedundantConnection(self, edges: list[list[int]]) -> list[int]:
        return solve(edges)
