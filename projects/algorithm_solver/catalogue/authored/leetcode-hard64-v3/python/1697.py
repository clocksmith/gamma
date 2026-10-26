"""1697. Checking Existence of Edge Length Limited Paths: offline increasing-limit DSU sweep; O((E+Q) log(E+Q)+n) time and O(n+E+Q) space."""


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


def solve(n: int, edgeList: list[list[int]], queries: list[list[int]]) -> list[bool]:
    ordered_edges = sorted(edgeList, key=lambda edge: edge[2])
    ordered_queries = sorted((limit, first, second, index)
                             for index, (first, second, limit) in enumerate(queries))
    groups = _DisjointSet(n)
    answers = [False] * len(queries)
    edge_index = 0
    for limit, first, second, index in ordered_queries:
        while edge_index < len(ordered_edges) and ordered_edges[edge_index][2] < limit:
            groups.union(ordered_edges[edge_index][0], ordered_edges[edge_index][1])
            edge_index += 1
        answers[index] = groups.find(first) == groups.find(second)
    return answers


class Solution:
    def distanceLimitedPathsExist(self, n: int, edgeList: list[list[int]], queries: list[list[int]]) -> list[bool]:
        return solve(n, edgeList, queries)
