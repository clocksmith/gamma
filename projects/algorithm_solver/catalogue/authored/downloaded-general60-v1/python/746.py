"""746. Min Cost Climbing Stairs (Easy).

Specification: https://leetcode.com/problems/min-cost-climbing-stairs/description/
"""


def solve(cost: list[int]) -> int:
    a, b = 0, 0
    for i in range(2, len(cost) + 1):
        a, b = b, min(a + cost[i - 2], b + cost[i - 1])
    return b


class Solution:
    def minCostClimbingStairs(self, cost: list[int]) -> int:
        return solve(cost)
