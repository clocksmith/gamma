"""1761. Minimum Degree of a Connected Trio in a Graph.

Enumerate triangles in an adjacency matrix; O(n^3) time, O(n^2) space. Inputs are preserved.
"""

def solve(n: int, edges: list[list[int]]) -> int:
    graph = [bytearray(n) for _ in range(n)]
    degree = [0] * n
    for a, b in edges:
        a -= 1
        b -= 1
        graph[a][b] = graph[b][a] = 1
        degree[a] += 1
        degree[b] += 1
    answer = float('inf')
    for a in range(n):
        for b in range(a + 1, n):
            if graph[a][b]:
                for c in range(b + 1, n):
                    if graph[a][c] and graph[b][c]:
                        answer = min(answer, degree[a] + degree[b] + degree[c] - 6)
    return -1 if answer == float('inf') else answer


class Solution:
    def minTrioDegree(self, n: int, edges: list[list[int]]) -> int:
        return solve(n, edges)
