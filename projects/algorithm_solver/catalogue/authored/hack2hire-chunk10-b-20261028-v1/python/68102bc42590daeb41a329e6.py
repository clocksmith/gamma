"""Hack2Hire 68102bc42590daeb41a329e6 (Equalize Server Latency) over an INFERRED spec; qualification unknown."""


def solve(n, latency):
    cost = list(latency)  # private copy: path sums accumulate here
    total = 0
    for v in range(n // 2 - 1, -1, -1):
        left, right = cost[2 * v + 1], cost[2 * v + 2]
        total += abs(left - right)
        cost[v] += max(left, right)
    return total


class Solution:
    def minIncrements(self, n, latency):
        return solve(n, latency)
