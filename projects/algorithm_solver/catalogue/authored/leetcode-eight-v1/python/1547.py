"""Interval dynamic programming over the sorted cut positions."""


def solve(n: int, cuts: list[int]) -> int:
    """O(m^3) time and O(m^2) space for m cuts; retain the original cut order."""
    positions = [0, *sorted(cuts), n]
    size = len(positions)
    cost = [[0] * size for _ in positions]
    for width in range(2, size):
        for left in range(size - width):
            right = left + width
            best = min(cost[left][cut] + cost[cut][right]
                       for cut in range(left + 1, right))
            cost[left][right] = positions[right] - positions[left] + best
    return cost[0][-1]


class Solution:
    def minCost(self, n: int, cuts: list[int]) -> int:
        return solve(n, cuts)
