"""2603. Collect Coins in a Tree. Prune coinless branches and then two complete outer layers."""

from collections import deque


def solve(coins: list[int], edges: list[list[int]]) -> int:
    """O(n) time and O(n) space. Inputs are preserved."""
    size = len(coins)
    graph = [[] for _ in coins]
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    degree = [len(neighbors) for neighbors in graph]
    remaining = len(edges)
    queue = deque(node for node in range(size) if degree[node] == 1 and coins[node] == 0)
    while queue:
        node = queue.popleft()
        if degree[node] == 0:
            continue
        degree[node] = 0
        for neighbor in graph[node]:
            if degree[neighbor] > 0:
                degree[neighbor] -= 1
                remaining -= 1
                if degree[neighbor] == 1 and coins[neighbor] == 0:
                    queue.append(neighbor)
    queue = deque(node for node in range(size) if degree[node] == 1)
    for _ in range(2):
        for _ in range(len(queue)):
            node = queue.popleft()
            if degree[node] == 0:
                continue
            degree[node] = 0
            for neighbor in graph[node]:
                if degree[neighbor] > 0:
                    degree[neighbor] -= 1
                    remaining -= 1
                    if degree[neighbor] == 1:
                        queue.append(neighbor)
    return 2 * remaining


class Solution:
    def collectTheCoins(self, coins: list[int], edges: list[list[int]]) -> int:
        return solve(coins, edges)
