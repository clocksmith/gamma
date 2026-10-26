"""3772. Maximum Subgraph Score in a Tree."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]], good: list[int]) -> list[int]:
    """O(n) time and O(n) space; iterative bottom-up and top-down rerooting."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)
    parent = [-1] * n
    order = [0]
    for node in order:
        for child in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    down = [2 * value - 1 for value in good]
    for node in reversed(order[1:]):
        down[parent[node]] += max(0, down[node])
    answer = down[:]
    for node in order[1:]:
        ancestor = parent[node]
        answer[node] += max(0, answer[ancestor] - max(0, down[node]))
    return answer


class Solution:
    def maxSubgraphScore(self, n: int, edges: list[list[int]], good: list[int]) -> list[int]:
        return solve(n, edges, good)
