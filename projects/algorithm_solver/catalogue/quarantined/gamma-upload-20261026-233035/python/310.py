"""310. Minimum Height Trees."""
from collections import deque

def solve(n: int, edges: list[list[int]]) -> list[int]:
    if n <= 2:
        return list(range(n))
    graph = [set() for _ in range(n)]
    for left, right in edges:
        graph[left].add(right)
        graph[right].add(left)
    leaves = deque(index for index in range(n) if len(graph[index]) == 1)
    remaining = n
    while remaining > 2:
        count = len(leaves)
        remaining -= count
        for _ in range(count):
            leaf = leaves.popleft()
            neighbor = graph[leaf].pop()
            graph[neighbor].remove(leaf)
            if len(graph[neighbor]) == 1:
                leaves.append(neighbor)
    return list(leaves)

class Solution:
    def findMinHeightTrees(self, n: int, edges: list[list[int]]) -> list[int]:
        return solve(n, edges)
