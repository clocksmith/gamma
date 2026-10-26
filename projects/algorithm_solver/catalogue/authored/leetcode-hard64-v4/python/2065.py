"""2065. Maximum Path Quality of a Graph."""

from heapq import heappop, heappush


def solve(values: list[int], edges: list[list[int]], maxTime: int) -> int:
    """Return-distance-pruned walk search; O(E log V+Delta^D) time, O(V+E+D) space, D<=10 in-domain. Inputs are preserved."""
    neighbors = [[] for _ in values]
    for first, second, duration in edges:
        neighbors[first].append((second, duration))
        neighbors[second].append((first, duration))
    home = [float('inf')] * len(values)
    home[0] = 0
    heap = [(0, 0)]
    while heap:
        elapsed, node = heappop(heap)
        if elapsed != home[node]:
            continue
        for target, duration in neighbors[node]:
            following = elapsed + duration
            if following < home[target]:
                home[target] = following
                heappush(heap, (following, target))
    visits = [0] * len(values)
    visits[0] = 1
    answer = values[0]

    def search(node, elapsed, quality):
        nonlocal answer
        if node == 0:
            answer = max(answer, quality)
        for target, duration in neighbors[node]:
            following = elapsed + duration
            if following + home[target] > maxTime:
                continue
            extra = values[target] if visits[target] == 0 else 0
            visits[target] += 1
            search(target, following, quality + extra)
            visits[target] -= 1

    search(0, 0, values[0])
    return answer


class Solution:
    def maximalPathQuality(self, values: list[int], edges: list[list[int]], maxTime: int) -> int:
        return solve(values, edges, maxTime)
