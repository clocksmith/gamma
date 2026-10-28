"""1514. Path with Maximum Probability (Medium).

Specification: https://leetcode.com/problems/path-with-maximum-probability/description/
"""


def solve(n: int, edges: list[list[int]], succProb: list[float], start: int, end: int) -> float:
    graph = [[] for _ in range(n)]
    for i, (a, b) in enumerate(edges):
        graph[a].append((b, succProb[i]))
        graph[b].append((a, succProb[i]))
    best = [0.0] * n
    best[start] = 1.0
    visited = [False] * n
    for _step in range(n):
        node = -1
        value = 0.0
        for i in range(n):
            if not visited[i] and best[i] > value:
                value = best[i]
                node = i
        if node == -1:
            break
        visited[node] = True
        for neighbor, prob in graph[node]:
            if best[node] * prob > best[neighbor]:
                best[neighbor] = best[node] * prob
    return best[end]


class Solution:
    def maxProbability(self, n: int, edges: list[list[int]], succProb: list[float], start: int, end: int) -> float:
        return solve(n, edges, succProb, start, end)
