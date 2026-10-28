"""983. Minimum Cost For Tickets (Medium).

Specification: https://leetcode.com/problems/minimum-cost-for-tickets/description/
"""


def solve(days: list[int], costs: list[int]) -> int:
    day_set = set(days)
    last = days[-1]
    dp = [0] * (last + 1)
    for day in range(1, last + 1):
        if day not in day_set:
            dp[day] = dp[day - 1]
        else:
            dp[day] = min(dp[day - 1] + costs[0], dp[max(0, day - 7)] + costs[1], dp[max(0, day - 30)] + costs[2])
    return dp[last]


class Solution:
    def mincostTickets(self, days: list[int], costs: list[int]) -> int:
        return solve(days, costs)
