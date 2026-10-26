"""3693. Climbing Stairs II."""
from __future__ import annotations


def solve(n: int, costs: list[int]) -> int:
    """O(n) time and O(1) auxiliary space; landing cost uses zero-based costs[step - 1]."""
    previous = [0, float('inf'), float('inf')]
    for step in range(1, n + 1):
        best = min(previous[0] + 1, previous[1] + 4, previous[2] + 9) + costs[step - 1]
        previous = [best, previous[0], previous[1]]
    return previous[0]


class Solution:
    def climbStairs(self, n: int, costs: list[int]) -> int:
        return solve(n, costs)
