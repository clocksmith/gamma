"""2959. Number of Possible Sets of Closing Branches.

Floyd-Warshall restricted to each surviving subset; O(2^n*n^3) time, O(n^2) space. Inputs are preserved.
"""

def solve(n: int, maxDistance: int, roads: list[list[int]]) -> int:
    base = [[float('inf')] * n for _ in range(n)]
    for node in range(n):
        base[node][node] = 0
    for first, second, weight in roads:
        base[first][second] = base[second][first] = min(base[first][second], weight)
    answer = 0
    for mask in range(1 << n):
        nodes = [node for node in range(n) if mask >> node & 1]
        distance = [row[:] for row in base]
        for middle in nodes:
            for first in nodes:
                for second in nodes:
                    distance[first][second] = min(distance[first][second], distance[first][middle] + distance[middle][second])
        if all(distance[first][second] <= maxDistance for first in nodes for second in nodes):
            answer += 1
    return answer


class Solution:
    def numberOfSets(self, n: int, maxDistance: int, roads: list[list[int]]) -> int:
        return solve(n, maxDistance, roads)
