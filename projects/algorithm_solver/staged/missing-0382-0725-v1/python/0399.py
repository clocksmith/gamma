"""399. Evaluate Division. Search a reciprocal weighted graph; inputs are preserved."""

from collections import defaultdict

def solve(equations: list[list[str]], values: list[float], queries: list[list[str]]) -> list[float]:
    graph = defaultdict(list)
    for (a, b), ratio in zip(equations, values):
        graph[a].append((b, ratio))
        graph[b].append((a, 1.0 / ratio))
    answer = []
    for source, target in queries:
        if source not in graph or target not in graph:
            answer.append(-1.0)
            continue
        stack = [(source, 1.0)]
        visited = {source}
        result = -1.0
        while stack:
            node, product = stack.pop()
            if node == target:
                result = product
                break
            for neighbor, ratio in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, product * ratio))
        answer.append(result)
    return answer


class Solution:
    def calcEquation(self, equations: list[list[str]], values: list[float], queries: list[list[str]]) -> list[float]:
        return solve(equations, values, queries)
