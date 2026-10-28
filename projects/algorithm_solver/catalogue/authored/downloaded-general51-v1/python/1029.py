"""1029. Two City Scheduling (Medium).

Specification: https://leetcode.com/problems/two-city-scheduling/description/
"""


def solve(costs: list[list[int]]) -> int:
    ordered = sorted(costs, key=lambda pair: pair[0] - pair[1])
    total = 0
    half = len(ordered) // 2
    for i, pair in enumerate(ordered):
        total += pair[0] if i < half else pair[1]
    return total


class Solution:
    def twoCitySchedCost(self, costs: list[list[int]]) -> int:
        return solve(costs)
