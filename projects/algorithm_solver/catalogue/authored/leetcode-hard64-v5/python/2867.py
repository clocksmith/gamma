"""2867. Count Valid Paths in a Tree. Merge non-prime components and connect their sizes across one prime node."""


def solve(n: int, edges: list[list[int]]) -> int:
    """O(n log log(n+2)+n*alpha(n)) time and O(n) space. Inputs are preserved."""
    prime = [True] * (n + 1)
    prime[0] = prime[1] = False
    factor = 2
    while factor * factor <= n:
        if prime[factor]:
            for multiple in range(factor * factor, n + 1, factor):
                prime[multiple] = False
        factor += 1
    graph = [[] for _ in range(n + 1)]
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
        if not prime[first] and not prime[second]:
            first, second = find(first), find(second)
            if first != second:
                if size[first] < size[second]:
                    first, second = second, first
                parent[second] = first
                size[first] += size[second]
    answer = 0
    for node in range(2, n + 1):
        if not prime[node]:
            continue
        seen = 0
        for neighbor in graph[node]:
            if not prime[neighbor]:
                count = size[find(neighbor)]
                answer += count * (seen + 1)
                seen += count
    return answer


class Solution:
    def countPaths(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
