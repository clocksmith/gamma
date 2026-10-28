"""886. Possible Bipartition (Medium).

Specification: https://leetcode.com/problems/possible-bipartition/description/
"""


def solve(n: int, dislikes: list[list[int]]) -> bool:
    graph = [[] for _ in range(n + 1)]
    for a, b in dislikes:
        graph[a].append(b)
        graph[b].append(a)
    color = [0] * (n + 1)
    for start in range(1, n + 1):
        if color[start] != 0:
            continue
        color[start] = 1
        queue = [start]
        while queue:
            node = queue.pop(0)
            for neighbor in graph[node]:
                if color[neighbor] == 0:
                    color[neighbor] = -color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False
    return True


class Solution:
    def possibleBipartition(self, n: int, dislikes: list[list[int]]) -> bool:
        return solve(n, dislikes)
