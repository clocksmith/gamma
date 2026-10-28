"""1627. Graph Connectivity With Threshold (Medium).

Specification: https://leetcode.com/problems/graph-connectivity-with-threshold/description/
"""


def solve(n: int, threshold: int, queries: list[list[int]]) -> list[bool]:
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for divisor in range(threshold + 1, n + 1):
        multiple = divisor * 2
        while multiple <= n:
            union(divisor, multiple)
            multiple += divisor
    return [find(a) == find(b) for a, b in queries]


class Solution:
    def areConnected(self, n: int, threshold: int, queries: list[list[int]]) -> list[bool]:
        return solve(n, threshold, queries)
