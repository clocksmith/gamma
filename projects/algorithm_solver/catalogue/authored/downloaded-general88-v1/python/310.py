"""310. Minimum Height Trees (Medium).

Specification: https://leetcode.com/problems/minimum-height-trees/description/
"""


def solve(n: int, edges: list[list[int]]) -> list[int]:
    if n == 1:
        return [0]
    graph = [[] for _ in range(n)]
    degree = [0] * n
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
        degree[a] += 1
        degree[b] += 1
    leaves = [i for i in range(n) if degree[i] == 1]
    remaining = n
    while remaining > 2:
        remaining -= len(leaves)
        next_leaves = []
        for leaf in leaves:
            for neighbor in graph[leaf]:
                degree[neighbor] -= 1
                if degree[neighbor] == 1:
                    next_leaves.append(neighbor)
        leaves = next_leaves
    return sorted(leaves)


class Solution:
    def findMinHeightTrees(self, n: int, edges: list[list[int]]) -> list[int]:
        return solve(n, edges)
