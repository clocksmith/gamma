"""1578. Minimum Deletion Cost to Avoid Repeating Letters (Medium).

Specification: https://leetcode.com/problems/minimum-deletion-cost-to-avoid-repeating-letters/description/
"""


def solve(s: str, cost: list[int]) -> int:
    cost = cost[:]
    total = 0
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            if cost[i] < cost[i - 1]:
                total += cost[i]
                cost[i] = cost[i - 1]
            else:
                total += cost[i - 1]
    return total


class Solution:
    def minCost(self, s: str, cost: list[int]) -> int:
        return solve(s, cost)
