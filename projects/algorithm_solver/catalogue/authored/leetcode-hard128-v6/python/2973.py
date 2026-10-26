"""2973. Find Number of Coins to Place in Tree Nodes.

Postorder aggregation retains only two minima and three maxima; O(n) time and space. Inputs are preserved.
"""

def solve(edges: list[list[int]], cost: list[int]) -> list[int]:
    n = len(cost)
    graph = [[] for _ in cost]
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    parent = [-1] * n
    order = [0]
    for node in order:
        for neighbor in graph[node]:
            if neighbor != parent[node]:
                parent[neighbor] = node
                order.append(neighbor)
    sizes = [1] * n
    extremes = [[] for _ in cost]
    answers = [1] * n
    for node in reversed(order):
        values = [cost[node]]
        for child in graph[node]:
            if parent[child] != node:
                continue
            sizes[node] += sizes[child]
            values = sorted(values + extremes[child])
            if len(values) > 5:
                values = values[:2] + values[-3:]
        extremes[node] = values
        if sizes[node] >= 3:
            answers[node] = max(0, values[-1] * values[-2] * values[-3], values[0] * values[1] * values[-1])
    return answers


class Solution:
    def placedCoins(self, edges: list[list[int]], cost: list[int]) -> list[int]:
        return solve(edges, cost)
