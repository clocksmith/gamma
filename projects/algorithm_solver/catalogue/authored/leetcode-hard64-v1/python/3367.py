"""3367. Maximize Sum of Weights after Edge Removals: iterative tree dynamic programming with positive child-edge gains."""


def solve(edges: list[list[int]], k: int) -> int:
    """O(n log n) time and O(n) auxiliary space. Inputs are preserved."""
    n = len(edges) + 1
    graph = [[] for _ in range(n)]
    for first, second, weight in edges:
        graph[first].append((second, weight))
        graph[second].append((first, weight))
    parent = [-1] * n
    order = [0]
    for node in order:
        for child, _ in graph[node]:
            if child != parent[node]:
                parent[child] = node
                order.append(child)
    free = [0] * n
    used = [0] * n
    for node in reversed(order):
        base = 0
        gains = []
        for child, weight in graph[node]:
            if parent[child] != node:
                continue
            base += free[child]
            gain = weight + used[child] - free[child]
            if gain > 0:
                gains.append(gain)
        gains.sort(reverse=True)
        free[node] = base + sum(gains[:k])
        used[node] = base + sum(gains[:k - 1]) if k else float('-inf')
    return free[0]


class Solution:
    def maximizeSumOfWeights(self, edges: list[list[int]], k: int) -> int:
        return solve(edges, k)
