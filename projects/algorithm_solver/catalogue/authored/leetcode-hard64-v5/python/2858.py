"""2858. Minimum Edge Reversals So Every Node Is Reachable. Count reversals from one root and reroot across each edge."""


def solve(n: int, edges: list[list[int]]) -> list[int]:
    """O(n) time and O(n) space. Inputs are preserved."""
    graph = [[] for _ in range(n)]
    for first, second in edges:
        graph[first].append((second, 0))
        graph[second].append((first, 1))
    parent = [-1] * n
    direction = [0] * n
    order = [0]
    baseline = 0
    for node in order:
        for neighbor, reversal in graph[node]:
            if neighbor == parent[node]:
                continue
            parent[neighbor] = node
            direction[neighbor] = reversal
            baseline += reversal
            order.append(neighbor)
    answer = [0] * n
    answer[0] = baseline
    for node in order[1:]:
        answer[node] = answer[parent[node]] + (1 if direction[node] == 0 else -1)
    return answer


class Solution:
    def minEdgeReversals(self, n: int, edges: list[list[int]]) -> list[int]:
        return solve(n, edges)
