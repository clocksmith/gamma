"""1334. Find the City With the Smallest Number of Neighbors at a Threshold Distance: compute all-pairs distances and resolve count ties toward the larger city."""


def solve(n: int, edges: list[list[int]], distanceThreshold: int) -> int:
    """O(n^3) time and O(n^2) auxiliary space; inputs are read-only."""
    distances = [[float('inf')] * n for _ in range(n)]
    for city in range(n):
        distances[city][city] = 0
    for left, right, weight in edges:
        distances[left][right] = min(distances[left][right], weight)
        distances[right][left] = min(distances[right][left], weight)
    for middle in range(n):
        for left in range(n):
            first = distances[left][middle]
            if first == float('inf'):
                continue
            for right in range(n):
                distances[left][right] = min(distances[left][right], first + distances[middle][right])
    answer = -1
    fewest = n
    for city in range(n):
        count = sum(other != city and distance <= distanceThreshold
                    for other, distance in enumerate(distances[city]))
        if count <= fewest:
            answer, fewest = city, count
    return answer


class Solution:
    def findTheCity(self, n: int, edges: list[list[int]], distanceThreshold: int) -> int:
        return solve(n, edges, distanceThreshold)
