"""Hack2Hire 684ba2bf4023c4f502877de9 (Find Defendency Bottleneck) over an INFERRED spec; qualification unknown."""


def solve(n, edges):
    out = [[] for _ in range(n)]
    indegree = [0] * n
    for u, v in edges:
        out[u].append(v)
        indegree[v] += 1
    frontier = [v for v in range(n) if indegree[v] == 0]
    bottlenecks = []
    while frontier:
        if len(frontier) == 1:
            bottlenecks.append(frontier[0])
        following = []
        for u in frontier:
            for v in out[u]:
                indegree[v] -= 1
                if indegree[v] == 0:
                    following.append(v)
        frontier = following
    return bottlenecks


class Solution:
    def findBottlenecks(self, n, edges):
        return solve(n, edges)
