"""1584. Min Cost to Connect All Points: run dense Prim without materializing the complete Manhattan graph."""


def solve(points: list[list[int]]) -> int:
    """O(n^2) time and O(n) auxiliary space; inputs are read-only."""
    size = len(points)
    distance = [float('inf')] * size
    distance[0] = 0
    used = [False] * size
    total = 0
    for _ in range(size):
        chosen = -1
        for node in range(size):
            if not used[node] and (chosen == -1 or distance[node] < distance[chosen]):
                chosen = node
        used[chosen] = True
        total += distance[chosen]
        x, y = points[chosen]
        for node in range(size):
            if not used[node]:
                cost = abs(x - points[node][0]) + abs(y - points[node][1])
                distance[node] = min(distance[node], cost)
    return total


class Solution:
    def minCostConnectPoints(self, points: list[list[int]]) -> int:
        return solve(points)
