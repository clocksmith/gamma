"""3786. Total Sum of Interaction Cost in Tree Groups."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]], group: list[int]) -> int:
    """O(20n) time and O(n) auxiliary space; charge each edge once for every same-group pair crossing it."""
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
    answer = 0
    for label in set(group):
        count = [int(value == label) for value in group]
        total = sum(count)
        for node in reversed(order[1:]):
            amount = count[node]
            answer += amount * (total - amount)
            count[parent[node]] += amount
    return answer


class Solution:
    def interactionCosts(self, n: int, edges: list[list[int]], group: list[int]) -> int:
        return solve(n, edges, group)
