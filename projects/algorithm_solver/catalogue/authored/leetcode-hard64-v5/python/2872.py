"""2872. Maximum Number of K-Divisible Components. Close every divisible subtree while accumulating remainders in iterative postorder."""


def solve(n: int, edges: list[list[int]], values: list[int], k: int) -> int:
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
    remainder = [value % k for value in values]
    answer = 0
    for node in reversed(order):
        if remainder[node] == 0:
            answer += 1
        elif parent[node] != -1:
            previous = parent[node]
            remainder[previous] = (remainder[previous] + remainder[node]) % k
    return answer


class Solution:
    def maxKDivisibleComponents(self, n: int, edges: list[list[int]], values: list[int], k: int) -> int:
        return solve(n, edges, values, k)
