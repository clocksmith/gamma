"""Hack2Hire 67ccb2bb3363b83a81fc996a (Maximize Edge Sum in Graph) over an INFERRED spec; qualification unknown."""


def solve(n, edges):
    degree = [0] * n
    for a, b in edges:
        degree[a] += 1
        degree[b] += 1
    degree.sort()
    total = 0
    for label in range(1, n + 1):
        total += label * degree[label - 1]
    return total


class Solution:
    def maximizeEdgeSum(self, n, edges):
        return solve(n, edges)
