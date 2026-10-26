"""3553. Minimum Weighted Subgraph With the Required Paths II.

The three-terminal subtree has half the sum of its three pairwise distances; binary lifting answers each distance; O((n+q) log n) time and O(n log n+q) space. Inputs are preserved.
"""

def solve(edges: list[list[int]], queries: list[list[int]]) -> list[int]:
    n = len(edges) + 1
    graph = [[] for _ in range(n)]
    for first, second, weight in edges:
        graph[first].append((second, weight))
        graph[second].append((first, weight))
    levels = n.bit_length()
    ancestor = [[0] * n for _ in range(levels)]
    depth, distance = [0] * n, [0] * n
    order = [0]
    for node in order:
        for child, weight in graph[node]:
            if child == ancestor[0][node]:
                continue
            ancestor[0][child] = node
            depth[child] = depth[node] + 1
            distance[child] = distance[node] + weight
            order.append(child)
    for level in range(1, levels):
        for node in range(n):
            ancestor[level][node] = ancestor[level - 1][ancestor[level - 1][node]]

    def lca(first, second):
        if depth[first] < depth[second]:
            first, second = second, first
        difference = depth[first] - depth[second]
        for level in range(levels):
            if difference & (1 << level):
                first = ancestor[level][first]
        if first == second:
            return first
        for level in range(levels - 1, -1, -1):
            if ancestor[level][first] != ancestor[level][second]:
                first, second = ancestor[level][first], ancestor[level][second]
        return ancestor[0][first]

    def path(first, second):
        return distance[first] + distance[second] - 2 * distance[lca(first, second)]

    return [(path(first, second) + path(first, destination) + path(second, destination)) // 2
            for first, second, destination in queries]


class Solution:
    def minimumWeight(self, edges: list[list[int]], queries: list[list[int]]) -> list[int]:
        return solve(edges, queries)
