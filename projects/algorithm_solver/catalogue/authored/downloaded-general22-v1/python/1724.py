"""1724. Checking Existence of Edge Length Limited Paths (Medium).

Specification: https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths/description/
"""


def solve(n: int, edgeList: list[list[int]], queries: list[list[int]]) -> list[bool]:
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = sorted(edgeList, key=lambda edge: edge[2])
    indexed = sorted(enumerate(queries), key=lambda item: item[1][2])
    answer = [False] * len(queries)
    e = 0
    for idx, (u, v, limit) in indexed:
        while e < len(edges) and edges[e][2] < limit:
            parent[find(edges[e][0])] = find(edges[e][1])
            e += 1
        answer[idx] = find(u) == find(v)
    return answer


class Solution:
    def distanceLimitedPathsExist(self, n: int, edgeList: list[list[int]], queries: list[list[int]]) -> list[bool]:
        return solve(n, edgeList, queries)
