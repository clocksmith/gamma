"""2673. Make Costs of Paths Equal in a Binary Tree: balance child path totals bottom-up in a private copy of the complete tree."""


def solve(n: int, cost: list[int]) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    totals = cost[:]
    increments = 0
    for node in range(n // 2 - 1, -1, -1):
        left, right = 2 * node + 1, 2 * node + 2
        increments += abs(totals[left] - totals[right])
        totals[node] += max(totals[left], totals[right])
    return increments


class Solution:
    def minIncrements(self, n: int, cost: list[int]) -> int:
        return solve(n, cost)
