"""2492. Minimum Score of a Path Between Two Cities: find the lightest edge in the connected component containing city one."""


def solve(n: int, roads: list[list[int]]) -> int:
    """O(n + e) time and O(n + e) auxiliary space; inputs are read-only."""
    graph = [[] for _ in range(n + 1)]
    for left, right, distance in roads:
        graph[left].append((right, distance))
        graph[right].append((left, distance))
    seen = [False] * (n + 1)
    seen[1] = True
    stack = [1]
    best = float('inf')
    while stack:
        node = stack.pop()
        for neighbor, distance in graph[node]:
            best = min(best, distance)
            if not seen[neighbor]:
                seen[neighbor] = True
                stack.append(neighbor)
    return int(best)


class Solution:
    def minScore(self, n: int, roads: list[list[int]]) -> int:
        return solve(n, roads)
