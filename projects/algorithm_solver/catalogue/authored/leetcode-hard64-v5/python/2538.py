"""2538. Difference Between Maximum and Minimum Price Sum. Iterative tree DP for paths with one endpoint price excluded."""


def solve(n: int, edges: list[list[int]], price: list[int]) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    parent = [-1] * n
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    included = price.copy()
    excluded = [0] * n
    answer = 0
    for node in reversed(order):
        for child in graph[node]:
            if parent[child] != node:
                continue
            answer = max(answer, included[node] + excluded[child], excluded[node] + included[child])
            included[node] = max(included[node], price[node] + included[child])
            excluded[node] = max(excluded[node], price[node] + excluded[child])
    return answer


class Solution:
    def maxOutput(self, n: int, edges: list[list[int]], price: list[int]) -> int:
        return solve(n, edges, price)
