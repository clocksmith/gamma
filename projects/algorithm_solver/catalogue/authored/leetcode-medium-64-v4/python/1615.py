"""1615. Maximal Network Rank: combine endpoint degrees and subtract their shared road once."""


def solve(n: int, roads: list[list[int]]) -> int:
    """O(n^2 + e) expected time and O(n + e) auxiliary space; inputs are read-only."""
    neighbors = [set() for _ in range(n)]
    for first, second in roads:
        neighbors[first].add(second)
        neighbors[second].add(first)
    best = 0
    for first in range(n):
        for second in range(first + 1, n):
            rank = len(neighbors[first]) + len(neighbors[second]) - (second in neighbors[first])
            best = max(best, rank)
    return best


class Solution:
    def maximalNetworkRank(self, n: int, roads: list[list[int]]) -> int:
        return solve(n, roads)
