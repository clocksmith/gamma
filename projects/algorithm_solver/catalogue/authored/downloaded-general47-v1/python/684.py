"""684. Redundant Connection (Medium).

Specification: https://leetcode.com/problems/redundant-connection/description/
"""


def solve(edges: list[list[int]]) -> list[int]:
    parent = {}

    def find(x):
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    for a, b in edges:
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            return [a, b]
        parent[root_a] = root_b
    return []


class Solution:
    def findRedundantConnection(self, edges: list[list[int]]) -> list[int]:
        return solve(edges)
