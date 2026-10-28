"""797. All Paths From Source to Target (Medium).

Specification: https://leetcode.com/problems/all-paths-from-source-to-target/description/
"""


def solve(graph: list[list[int]]) -> list[list[int]]:
    result = []
    target = len(graph) - 1

    def dfs(node, path):
        if node == target:
            result.append(path[:])
            return
        for nxt in graph[node]:
            path.append(nxt)
            dfs(nxt, path)
            path.pop()

    dfs(0, [0])
    return result


class Solution:
    def allPathsSourceTarget(self, graph: list[list[int]]) -> list[list[int]]:
        return solve(graph)
