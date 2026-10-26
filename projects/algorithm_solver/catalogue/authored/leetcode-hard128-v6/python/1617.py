"""1617. Count Subtrees With Max Distance Between Cities.

Enumerate induced subsets of a tree and use all-pairs distances; O(n^2 * 2^n) time, O(n^2 + 2^n) space. Inputs are preserved.
"""

from collections import deque


def solve(n: int, edges: list[list[int]]) -> list[int]:
    graph = [[] for _ in range(n)]
    pairs = [(a - 1, b - 1) for a, b in edges]
    for a, b in pairs:
        graph[a].append(b)
        graph[b].append(a)
    distances = [[-1] * n for _ in range(n)]
    for start in range(n):
        distances[start][start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in graph[node]:
                if distances[start][neighbor] == -1:
                    distances[start][neighbor] = distances[start][node] + 1
                    queue.append(neighbor)
    answer = [0] * (n - 1)
    for mask in range(1, 1 << n):
        count = mask.bit_count()
        if count < 2 or sum(bool(mask & (1 << a)) and bool(mask & (1 << b)) for a, b in pairs) != count - 1:
            continue
        diameter = 0
        for a in range(n):
            if mask & (1 << a):
                for b in range(a + 1, n):
                    if mask & (1 << b):
                        diameter = max(diameter, distances[a][b])
        answer[diameter - 1] += 1
    return answer


class Solution:
    def countSubgraphsForEachDiameter(self, n: int, edges: list[list[int]]) -> list[int]:
        return solve(n, edges)
