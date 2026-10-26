"""3820. Pythagorean Distance Nodes in a Tree."""
from __future__ import annotations


def solve(n: int, edges: list[list[int]], x: int, y: int, z: int) -> int:
    """O(n) time and space; three iterative traversals, including valid zero-distance triples."""
    graph = [[] for _ in range(n)]
    for left, right in edges:
        graph[left].append(right)
        graph[right].append(left)

    def distances(origin):
        result = [-1] * n
        result[origin] = 0
        queue = [origin]
        for node in queue:
            for child in graph[node]:
                if result[child] < 0:
                    result[child] = result[node] + 1
                    queue.append(child)
        return result

    rows = [distances(origin) for origin in (x, y, z)]
    answer = 0
    for index in range(n):
        a, b, c = sorted(row[index] for row in rows)
        if a * a + b * b == c * c:
            answer += 1
    return answer


class Solution:
    def specialNodes(self, n: int, edges: list[list[int]], x: int, y: int, z: int) -> int:
        return solve(n, edges, x, y, z)
