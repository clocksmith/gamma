"""2846. Minimum Edge Weight Equilibrium Queries in a Tree. Binary-lifting LCA and root-prefix counts for the 26 edge weights."""


def solve(n: int, edges: list[list[int]], queries: list[list[int]]) -> list[int]:
    """O((n+q)*(log(n+1)+26)) time and O(n*(log(n+1)+26)) auxiliary space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second, weight in edges:
        graph[first].append((second, weight - 1))
        graph[second].append((first, weight - 1))
    levels = max(1, n.bit_length())
    ancestor = [[0] * n for _ in range(levels)]
    depth = [-1] * n
    depth[0] = 0
    counts = [[0] * 26 for _ in range(n)]
    order = [0]
    for node in order:
        for neighbor, weight in graph[node]:
            if depth[neighbor] != -1:
                continue
            ancestor[0][neighbor] = node
            depth[neighbor] = depth[node] + 1
            counts[neighbor] = counts[node].copy()
            counts[neighbor][weight] += 1
            order.append(neighbor)
    for level in range(1, levels):
        for node in range(n):
            ancestor[level][node] = ancestor[level - 1][ancestor[level - 1][node]]

    def common_ancestor(first, second):
        if depth[first] < depth[second]:
            first, second = second, first
        difference = depth[first] - depth[second]
        for level in range(levels):
            if difference >> level & 1:
                first = ancestor[level][first]
        if first == second:
            return first
        for level in range(levels - 1, -1, -1):
            if ancestor[level][first] != ancestor[level][second]:
                first = ancestor[level][first]
                second = ancestor[level][second]
        return ancestor[0][first]

    answer = []
    for first, second in queries:
        common = common_ancestor(first, second)
        length = depth[first] + depth[second] - 2 * depth[common]
        largest = max(counts[first][weight] + counts[second][weight] - 2 * counts[common][weight]
                      for weight in range(26))
        answer.append(length - largest)
    return answer


class Solution:
    def minOperationsQueries(self, n: int, edges: list[list[int]], queries: list[list[int]]) -> list[int]:
        return solve(n, edges, queries)
