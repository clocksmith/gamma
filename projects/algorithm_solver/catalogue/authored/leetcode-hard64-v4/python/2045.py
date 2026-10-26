"""2045. Second Minimum Time to Reach Destination."""

from collections import deque


def solve(n: int, edges: list[list[int]], time: int, change: int) -> int:
    """Two distinct BFS hop counts, then synchronized-light timing; O(V+E) time and space. Inputs are preserved."""
    neighbors = [[] for _ in range(n + 1)]
    for first, second in edges:
        neighbors[first].append(second)
        neighbors[second].append(first)
    first = [float('inf')] * (n + 1)
    second = [float('inf')] * (n + 1)
    first[1] = 0
    queue = deque([(1, 0)])
    while queue:
        node, distance = queue.popleft()
        if node == n and distance == second[n]:
            elapsed = 0
            for _ in range(distance):
                phase = elapsed // change
                if phase % 2:
                    elapsed = (phase + 1) * change
                elapsed += time
            return elapsed
        following = distance + 1
        for target in neighbors[node]:
            if following < first[target]:
                first[target] = following
                queue.append((target, following))
            elif first[target] < following < second[target]:
                second[target] = following
                queue.append((target, following))
    return -1


class Solution:
    def secondMinimum(self, n: int, edges: list[list[int]], time: int, change: int) -> int:
        return solve(n, edges, time, change)
