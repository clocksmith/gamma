"""1579. Remove Max Number of Edges to Keep Graph Fully Traversable: shared edges before private edges using two DSUs; O((n+E)*alpha(n)) time and O(n) space."""


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


def solve(n: int, edges: list[list[int]]) -> int:
    alice, bob = _DisjointSet(n), _DisjointSet(n)
    retained = 0
    for kind, first, second in edges:
        if kind == 3:
            alice_added = alice.union(first - 1, second - 1)
            bob_added = bob.union(first - 1, second - 1)
            retained += int(alice_added or bob_added)
    for kind, first, second in edges:
        if kind == 1:
            retained += int(alice.union(first - 1, second - 1))
        elif kind == 2:
            retained += int(bob.union(first - 1, second - 1))
    if alice.components != 1 or bob.components != 1:
        return -1
    return len(edges) - retained


class Solution:
    def maxNumEdgesToRemove(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
