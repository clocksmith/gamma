"""785. Is Graph Bipartite? (Medium).

Specification: https://leetcode.com/problems/is-graph-bipartite/description/
"""


def solve(graph: list[list[int]]) -> bool:
    color = [-1] * len(graph)
    for start in range(len(graph)):
        if color[start] != -1:
            continue
        color[start] = 0
        queue = [start]
        while queue:
            node = queue.pop(0)
            for neighbor in graph[node]:
                if color[neighbor] == -1:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False
    return True


class Solution:
    def isBipartite(self, graph: list[list[int]]) -> bool:
        return solve(graph)
