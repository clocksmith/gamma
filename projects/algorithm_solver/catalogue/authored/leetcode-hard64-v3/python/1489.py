"""1489. Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree: forced/excluded-edge Kruskal runs; O(E^2*alpha(n) + E log E) time and O(n+E) space."""


class _DisjointSet:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.weight = [1] * size
        self.components = size

    def find(self, node: int) -> int:
        while node != self.parent[node]:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, first: int, second: int) -> bool:
        left, right = self.find(first), self.find(second)
        if left == right:
            return False
        if self.weight[left] < self.weight[right]:
            left, right = right, left
        self.parent[right] = left
        self.weight[left] += self.weight[right]
        self.components -= 1
        return True


def solve(n: int, edges: list[list[int]]) -> list[list[int]]:
    ordered = sorted((weight, first, second, index) for index, (first, second, weight) in enumerate(edges))

    def spanning(skip: int = -1, force: int = -1):
        groups = _DisjointSet(n)
        total = 0
        if force >= 0:
            first, second, weight = edges[force]
            if groups.union(first, second):
                total += weight
        for weight, first, second, index in ordered:
            if index != skip and groups.union(first, second):
                total += weight
        return total if groups.components == 1 else float('inf')

    baseline = spanning()
    critical, optional = [], []
    for index in range(len(edges)):
        if spanning(skip=index) > baseline:
            critical.append(index)
        elif spanning(force=index) == baseline:
            optional.append(index)
    return [critical, optional]


class Solution:
    def findCriticalAndPseudoCriticalEdges(self, n: int, edges: list[list[int]]) -> list[list[int]]:
        return solve(n, edges)
